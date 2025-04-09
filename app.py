# skill_gap_analyzer_app.py

import streamlit as st
import fitz  # PyMuPDF
import requests
import os
import json

# Load Together.ai API Key securely from Streamlit Secrets or env
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY") or "6dbe5caf57bf8bd1229c1e8db65c5b2264057440407563f1ef7c9fbd25c497bc"

# Load roles and skills from JSON
json_path = "roles_and_skills.json"
if not os.path.exists(json_path):
    st.error("Missing roles_and_skills.json. Make sure the file is in your app directory.")
    st.stop()

with open(json_path) as f:
    ROLE_SKILL_MAP = json.load(f)

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
    try:
        result = response.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        st.error("Something went wrong with the Together.ai response. Please try again.")
        return ""

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
    expected = ROLE_SKILL_MAP.get(role)
    if not expected:
        st.warning("Role not found in database. Using AI to infer expected skills.")
        prompt = f"List 10 most important skills for a {role} in 2025."
        ai_skills = ask_together(prompt)
        return [s.strip() for s in ai_skills.split(",") if s.strip().lower() not in [sk.lower() for sk in skills]]
    skills_lower = [s.lower() for s in skills]
    return [s for s in expected if s.lower() not in skills_lower]

def get_learning_recommendations(missing_skills):
    prompt = f"The user is missing these skills: {missing_skills}. Suggest ways to learn them."
    return ask_together(prompt)

def get_resume_tip_for_skill(skill):
    prompt = f"I have this skill: {skill}. Suggest how I can add this to my resume and LinkedIn profile."
    return ask_together(prompt)

# Streamlit App
st.set_page_config(page_title="Skill Gap Analyzer", layout="wide")
st.title("🧠 Skill Gap Analyzer Bot (Powered by Together.ai)")
st.image("Skill_Gap_Infographic.png", use_container_width=True)

st.markdown("Welcome! This tool helps you identify skill gaps between your current resume and your target role. Just select a role from the dropdown and upload your resume to begin 🚀")

role = st.selectbox("Select your target role", ["Select a role"] + list(ROLE_SKILL_MAP.keys()))
uploaded_file = st.file_uploader("Upload your resume (PDF)", type="pdf")

# Step tracker UX adjustment
if role and role != "Select a role":
    st.success("✅ Step 1: Target role selected")
if uploaded_file:
    st.success("✅ Step 2: Resume uploaded")

if uploaded_file and role and role != "Select a role":
    col1, col2 = st.columns([3, 1])
    with col1:
        run_analysis = st.button("🔍 Run Skill Gap Analysis", type="primary")
    with col2:
        if st.button("🔄 Reset"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.experimental_rerun()

    if run_analysis:
        with st.spinner("⏳ Extracting skills and checking against role requirements..."):
            resume_text = extract_text_from_pdf(uploaded_file)
            skill_output = get_skills_from_resume(resume_text)
            if skill_output:
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

                    st.success("✅ Step 4: Learning recommendations complete")

                    st.markdown("---")
                    st.markdown("### 🛠 Already have one of these skills?")

                    with st.form("resume_update_form"):
                        claimed = st.text_input("Which skill do you already have?")
                        submitted = st.form_submit_button("✍️ Generate Resume + LinkedIn Suggestion", type="primary")
                        if submitted:
                            if claimed and claimed.strip().lower() != "none":
                                fix = get_resume_tip_for_skill(claimed)
                                st.subheader("🪪 Resume + LinkedIn Suggestions")
                                st.write(fix)
                            else:
                                st.warning("Please enter a valid skill.")
