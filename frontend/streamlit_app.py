import json

import pandas as pd
import requests
import streamlit as st

API_URL = st.secrets.get("api_url", "http://localhost:8000")

st.set_page_config(page_title="AI Job Match & Resume Ranker", layout="wide")

st.markdown(
    """
    <style>
        .stApp { background: linear-gradient(145deg, #0f172a, #1e293b); color: #f8fafc; }
        .block-container { padding-top: 1.5rem; }
        .metric-card { background: rgba(15,23,42,0.75); border: 1px solid #334155; border-radius: 16px; padding: 1rem; }
        .title { font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem; color: #e2e8f0; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="title">AI Job Match & Resume Ranker</div>', unsafe_allow_html=True)
view = st.sidebar.radio("Choose View", ["Candidate View", "Recruiter View", "History"])

if view == "Candidate View":
    st.subheader("Candidate Analysis")
    col1, col2 = st.columns(2)

    with col1:
        candidate_name = st.text_input("Candidate Name")
        resume_file = st.file_uploader("Upload Resume (PDF/DOCX)", type=["pdf", "docx"])

    with col2:
        job_title = st.text_input("Job Title", value="AI Engineer")
        job_description = st.text_area("Paste Job Description", height=220)

    if st.button("Analyze Match", type="primary"):
        if not candidate_name or not resume_file or not job_description:
            st.error("Please fill all fields.")
        else:
            files = {"resume": (resume_file.name, resume_file.getvalue(), resume_file.type)}
            data = {
                "candidate_name": candidate_name,
                "job_title": job_title,
                "job_description": job_description,
            }
            res = requests.post(f"{API_URL}/analyze", files=files, data=data, timeout=30)
            if res.status_code != 200:
                st.error(res.text)
            else:
                payload = res.json()
                st.session_state["last_analysis"] = payload
                st.metric("Match Percentage", f"{payload['match_percentage']}%")
                st.progress(min(int(payload["match_percentage"]), 100))

                m1, m2, m3 = st.columns(3)
                m1.metric("Embedding Similarity", f"{payload['embedding_similarity']}%")
                m2.metric("Skill Match", f"{payload['skill_match_score']}%")
                m3.metric("Experience Score", f"{payload['experience_match_score']}%")

                st.write("### Missing Skills")
                st.write(", ".join(payload["missing_skills"]) if payload["missing_skills"] else "None")

                st.write("### AI Suggestions")
                for suggestion in payload["suggestions"]:
                    st.write(f"- {suggestion}")

                report_data = {
                    "candidate_name": payload["candidate_name"],
                    "match_score": payload["match_percentage"],
                    "matched_skills": ",".join(payload["matched_skills"]),
                    "missing_skills": ",".join(payload["missing_skills"]),
                    "suggestions": "|".join(payload["suggestions"]),
                    "recommendation": payload["recommendation"],
                }
                pdf = requests.post(f"{API_URL}/report", data=report_data, timeout=30)
                if pdf.status_code == 200:
                    st.download_button(
                        "Download PDF Report",
                        data=pdf.content,
                        file_name=f"{payload['candidate_name'].replace(' ', '_')}_report.pdf",
                        mime="application/pdf",
                    )

elif view == "Recruiter View":
    st.subheader("Recruiter Dashboard")
    resumes = st.file_uploader("Upload Multiple Resumes", type=["pdf", "docx"], accept_multiple_files=True)
    candidate_names = st.text_input("Candidate Names (comma separated)")
    job_description = st.text_area("Job Description", height=200)

    if st.button("Rank Candidates", type="primary"):
        if not resumes or not candidate_names or not job_description:
            st.warning("Please provide resumes, candidate names and job description.")
        else:
            files = [("resumes", (file.name, file.getvalue(), file.type)) for file in resumes]
            data = {
                "candidate_names": candidate_names,
                "job_description": job_description,
            }
            response = requests.post(f"{API_URL}/rank", files=files, data=data, timeout=60)
            if response.status_code != 200:
                st.error(response.text)
            else:
                rank_data = response.json()["rankings"]
                df = pd.DataFrame(rank_data)
                st.dataframe(df, use_container_width=True)
                selected = st.selectbox("Select candidate for detail", options=df["candidate_name"].tolist())
                detail = df[df["candidate_name"] == selected].iloc[0]
                st.json(json.loads(detail.to_json()))

else:
    st.subheader("Recent Analysis History")
    history_res = requests.get(f"{API_URL}/history", timeout=20)
    if history_res.status_code == 200:
        history_df = pd.DataFrame(history_res.json())
        st.dataframe(history_df, use_container_width=True)
    else:
        st.error("Could not load history")
