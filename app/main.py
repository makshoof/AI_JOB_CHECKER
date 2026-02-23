import json
import re
from typing import List

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.schemas import AnalyzeResponse, AnalysisHistoryItem, RankedCandidate, RankedResponse
from app.db.database import Base, engine, get_db
from app.db.models import Analysis, JobDescription, Resume
from app.services.ai_logic import EmbeddingService, calculate_match
from app.services.parsing import (
    TECHNICAL_SKILLS,
    TOOLS,
    extract_education,
    extract_text_from_file,
    extract_years_of_experience,
    find_keywords,
)
from app.services.reporting import generate_report

app = FastAPI(title="AI Job Match & Resume Ranker")
Base.metadata.create_all(bind=engine)
embedding_service = EmbeddingService()


def parse_required_years(jd_text: str) -> float:
    pattern = re.compile(r"(\d{1,2})\+?\s*(?:years|yrs)", re.IGNORECASE)
    years = [int(m.group(1)) for m in pattern.finditer(jd_text)]
    return float(max(years) if years else 0.0)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_resume(
    resume: UploadFile = File(...),
    candidate_name: str = Form(...),
    job_description: str = Form(...),
    job_title: str = Form("Untitled JD"),
    db: Session = Depends(get_db),
):
    content = await resume.read()
    try:
        resume_text = extract_text_from_file(resume.filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    resume_years = extract_years_of_experience(resume_text)
    jd_years = parse_required_years(job_description)

    result = calculate_match(
        resume_text=resume_text,
        jd_text=job_description,
        resume_years=resume_years,
        required_years=jd_years,
        embedding_service=embedding_service,
    )

    resume_record = Resume(
        candidate_name=candidate_name,
        file_name=resume.filename,
        raw_text=resume_text,
        extracted_skills=json.dumps(find_keywords(resume_text, TECHNICAL_SKILLS)),
        extracted_tools=json.dumps(find_keywords(resume_text, TOOLS)),
        years_experience=resume_years,
        education=extract_education(resume_text),
    )
    jd_record = JobDescription(
        title=job_title,
        raw_text=job_description,
        required_skills=json.dumps(find_keywords(job_description, TECHNICAL_SKILLS)),
        required_tools=json.dumps(find_keywords(job_description, TOOLS)),
        min_years_experience=jd_years,
    )
    db.add_all([resume_record, jd_record])
    db.flush()

    analysis = Analysis(
        resume_id=resume_record.id,
        job_description_id=jd_record.id,
        embedding_similarity=result.embedding_similarity,
        skill_match_score=result.skill_match_score,
        experience_match_score=result.experience_match_score,
        final_score=result.final_score,
        missing_skills=json.dumps(result.missing_skills),
        suggestions=json.dumps(result.suggestions),
    )
    db.add(analysis)
    db.commit()

    return AnalyzeResponse(
        candidate_name=candidate_name,
        match_percentage=result.final_score,
        embedding_similarity=result.embedding_similarity,
        skill_match_score=result.skill_match_score,
        experience_match_score=result.experience_match_score,
        matched_skills=result.matched_skills,
        missing_skills=result.missing_skills,
        suggestions=result.suggestions,
        recommendation=result.recommendation,
    )


@app.post("/rank", response_model=RankedResponse)
async def rank_resumes(
    resumes: List[UploadFile] = File(...),
    candidate_names: str = Form(...),
    job_description: str = Form(...),
):
    names = [name.strip() for name in candidate_names.split(",") if name.strip()]
    if len(names) != len(resumes):
        raise HTTPException(status_code=400, detail="candidate_names count must match resumes count")

    jd_years = parse_required_years(job_description)
    rankings: list[RankedCandidate] = []

    for idx, resume_file in enumerate(resumes):
        text = extract_text_from_file(resume_file.filename, await resume_file.read())
        score = calculate_match(text, job_description, extract_years_of_experience(text), jd_years, embedding_service)
        rankings.append(
            RankedCandidate(
                candidate_name=names[idx],
                match_percentage=score.final_score,
                skill_match_percentage=score.skill_match_score,
                experience_score=score.experience_match_score,
                analysis_id=idx + 1,
            )
        )

    rankings.sort(key=lambda candidate: candidate.match_percentage, reverse=True)
    return RankedResponse(rankings=rankings)


@app.get("/history", response_model=list[AnalysisHistoryItem])
def analysis_history(db: Session = Depends(get_db)):
    records = db.query(Analysis).order_by(Analysis.created_at.desc()).limit(20).all()
    history = [
        AnalysisHistoryItem(
            analysis_id=record.id,
            candidate_name=record.resume.candidate_name,
            final_score=record.final_score,
            created_at=record.created_at,
        )
        for record in records
    ]
    return history


@app.post("/report")
async def download_pdf_report(
    candidate_name: str = Form(...),
    match_score: float = Form(...),
    matched_skills: str = Form(""),
    missing_skills: str = Form(""),
    suggestions: str = Form(""),
    recommendation: str = Form("Needs Improvement"),
):
    report = generate_report(
        candidate_name=candidate_name,
        match_score=match_score,
        matched_skills=[s.strip() for s in matched_skills.split(",") if s.strip()],
        missing_skills=[s.strip() for s in missing_skills.split(",") if s.strip()],
        suggestions=[s.strip() for s in suggestions.split("|") if s.strip()],
        recommendation=recommendation,
    )
    return Response(
        content=report,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={candidate_name.replace(' ', '_')}_report.pdf"},
    )
