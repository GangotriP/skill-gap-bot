import streamlit as st
import fitz  # PyMuPDF
import requests
import tiktoken # For token counting

# 🔑 Your Together.ai API key here
TOGETHER_API_KEY = "6dbe5caf57bf8bd1229c1e8db65c5b2264057440407563f1ef7c9fbd25c497bc"  # ← Replace this with your real key

# 🧠 Call Together.ai's API for chat completion
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

    # Rough token estimate
    num_input_tokens = len(prompt.split()) * 1.3
    num_output_tokens = len(result.split()) * 1.3
    total_tokens = int(num_input_tokens + num_output_tokens)

    # Cost estimate for Mixtral ($0.0005 per 1K tokens)
    estimated_cost = (total_tokens / 1000) * 0.0005

    st.caption(f"🧮 Estimated tokens used: {total_tokens}")
    st.caption(f"💵 Estimated cost: ${estimated_cost:.4f} (Mixtral model)")

    return result


# 📄 Extract text from PDF
def extract_text_from_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# 🎯 Get skills from resume using LLM
def get_skills_from_resume(text):
    prompt = f"Extract a list of professional skills from this resume:\n\n{text}"
    return ask_together(prompt)

# 📊 Compare resume skills to role expectations
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

# 🎓 Get learning recommendations
def get_learning_recommendations(missing_skills):
    prompt = f"The user is missing these skills: {missing_skills}. Suggest ways to learn them."
    return ask_together(prompt)

# ✍️ Suggest resume and LinkedIn updates
def get_resume_tip_for_skill(skill):
    prompt = f"I have this skill: {skill}. Suggest how I can add this to my resume and LinkedIn profile."
    return ask_together(prompt)

# 🚀 Streamlit UI
st.title("🧠 Skill Gap Analyzer Bot (Powered by Together.ai)")

uploaded_file = st.file_uploader("Upload your resume (PDF)", type="pdf")

role = st.selectbox(
    "Select your target role",
    ["Instructional Designer", "Technical Program Manager", "Product Manager", "Data Analyst"]
)

if uploaded_file and role:
    resume_text = extract_text_from_pdf(uploaded_file)
    skill_output = get_skills_from_resume(resume_text)
    extracted_skills = [skill.strip() for skill in skill_output.split(",")]

    st.subheader("✅ Skills Found in Resume")
    st.write(extracted_skills)

    missing_skills = compare_with_role(extracted_skills, role)

    st.subheader("🚨 Skills You’re Missing for This Role")
    st.write(missing_skills)

    if missing_skills:
        tips = get_learning_recommendations(missing_skills)
        st.subheader("📚 Learning Recommendations")
        st.write(tips)

    if st.checkbox("I actually have one of these missing skills!"):
        claimed = st.text_input("Which skill?")
        if claimed:
            fix = get_resume_tip_for_skill(claimed)
            st.subheader("✍️ Resume + LinkedIn Suggestions")
            st.write(fix)