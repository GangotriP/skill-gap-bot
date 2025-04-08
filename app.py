# skill_gap_analyzer_app.py

import streamlit as st
import fitz  # PyMuPDF
import requests
import os

# Load Together.ai API Key securely from Streamlit Secrets or env
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY") or "your-key-here"

# Call Together.ai for responses
def ask_together(prompt):
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post("https://api.together.xyz/v1/chat/completions", headers=headers, json=data)
    result = response.json()["choices"][0]["message"]["content"]

    # Estimate token usage and cost
    num_input_tokens = len(prompt.split()) * 1.3
    num_output_tokens = len(result.split()) * 1.3
    total_tokens = int(num_input_tokens + num_output_tokens)
    estimated_cost = (total_tokens / 1000) * 0.0005

    st.caption(f"🧮 Estimated tokens used: {total_tokens}")
    st.caption(f"💵 Estimated cost: ${estimated_cost:.4f} (Mixtral model)")

    return result

# Extract resume text
def extract_text_from_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Extract skills from resume
def get_skills_from_resume(text):
    prompt = f"Extract a list of professional skills from this resume:\n\n{text}"
    return ask_together(prompt)

# Match extracted skills with expected skills per role
def compare_with_role(skills, role):
    expected = {
        "Instructional Designer": [
            "instructional design", "addie", "articulate storyline", "lms", "scorm",
            "training needs analysis", "kirkpatrick", "elearning", "job aids",
            "video scripting", "stakeholder management", "customer training", "support enablement"
        ],
        "Technical Program Manager": [
            "program management", "agile", "jira", "confluence", "roadmaps",
            "cross-functional collaboration", "technical specifications",
            "data analysis", "process automation", "kpis", "business intelligence",
            "risk management", "tool implementation", "okrs"
        ],
        "Product Manager": [
            "roadmapping", "jira", "a/b testing", "sql", "stakeholder management", "analytics"
        ],
        "Data Analyst": [
            "sql", "excel", "tableau", "python", "statistics"
        ]
    }
    skills_lower = [s.lower() for s in skills]
    return [s for s in expected[role] if s not in skills_lower]

def get_learning_recommendations(missing_skills):
    prompt = f"The user is missing these skills: {missing_skills}. Suggest ways to learn them."
    return ask_together(prompt)

def get_resume_tip_for_skill(skill):
    prompt = f"I have this skill: {skill}. Suggest how I can add this to my resume and LinkedIn profile."
    return ask_together(prompt)

# Streamlit App
st.set_page_config(page_title="Skill Gap Analyzer", layout="wide")
st.title("🧠 Skill Gap Analyzer Bot (Powered by Together.ai)")
st.image("A_colorful_2D_digital_infographic_titled_\"Skill_Ga.png", use_column_width=True)

st.markdown("Welcome! This tool helps you identify skill gaps between your current resume and your target role. Just upload your resume to begin 🚀")

# Reset button
if st.button("🔄 Reset"):
    st.experimental_rerun()

uploaded_file = st.file_uploader("Upload your resume (PDF)", type="pdf")
role = st.selectbox("Select your target role", ["Instructional Designer", "Technical Program Manager", "Product Manager", "Data Analyst"])

# Step tracker
if uploaded_file:
    st.success("✅ Step 1: Resume uploaded")
if role:
    st.success("✅ Step 2: Target role selected")

if uploaded_file and role:
    if st.button("🔍 Run Skill Gap Analysis"):
        resume_text = extract_text_from_pdf(uploaded_file)
        skill_output = get_skills_from_resume(resume_text)
        extracted_skills = [skill.strip() for skill in skill_output.split(",")]

        st.subheader("✅ Skills Found in Resume")
        st.write(extracted_skills)

        missing_skills = compare_with_role(extracted_skills, role)

        st.subheader("🚨 Skills You’re Missing for This Role")
        if missing_skills:
            st.markdown("\n".join([f"🔸 {skill}" for skill in missing_skills]))
        else:
            st.success("🎉 You have all the expected skills!")

        if missing_skills:
            st.success("✅ Step 3: Skill gap identified")
            tips = get_learning_recommendations(missing_skills)
            st.subheader("📚 Learning Recommendations")
            st.write(tips)

            st.markdown("---")
            st.markdown("### 🛠 Already have one of these skills?")
            if st.button("✅ I have one of these!"):
                claimed = st.text_input("Which skill do you already have?")
                if claimed and st.button("✍️ Generate Resume + LinkedIn Suggestion"):
                    fix = get_resume_tip_for_skill(claimed)
                    st.subheader("🪪 Resume + LinkedIn Suggestions")
                    st.write(fix)

        st.success("✅ Step 4: Analysis complete")
