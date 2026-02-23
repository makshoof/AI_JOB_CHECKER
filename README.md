# AI Job Match & Resume Ranker

Production-oriented web app for matching resumes against job descriptions, scoring candidates, and generating recruiter-ready PDF reports.

## Features
- Upload resume (`PDF` / `DOCX`) and paste job description.
- AI-powered scoring with weighted formula:
  - `0.5 × Embedding Similarity`
  - `0.3 × Skill Match Score`
  - `0.2 × Experience Match Score`
- Missing skill detection and improvement suggestions.
- Recruiter ranking view for multiple resumes.
- SQLite-backed history of analyses.
- Professional PDF report generation.

## Tech Stack
- Backend: FastAPI + SQLAlchemy + SQLite
- AI: Sentence Transformers (with TF-IDF fallback) + scikit-learn cosine similarity
- Parsing: pdfplumber + python-docx
- Frontend: Streamlit premium dark SaaS style

## Project Structure
```
app/
  api/schemas.py
  core/config.py
  db/database.py
  db/models.py
  services/ai_logic.py
  services/parsing.py
  services/reporting.py
  main.py
frontend/
  streamlit_app.py
data/samples/
tests/
```

## Run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
streamlit run frontend/streamlit_app.py
```

## Sample Job Description
See `data/samples/sample_job_description.txt`.

## Sample Resume
See `data/samples/sample_resume.txt`.

## Example Output
- Match Percentage: `82.4%`
- Matched Skills: `python, fastapi, aws, communication`
- Missing Skills: `kubernetes, mentoring`
- Recommendation: `Strong Fit`

## Performance
Single resume analysis completes in under 3 seconds in normal local environments with cached embeddings.
