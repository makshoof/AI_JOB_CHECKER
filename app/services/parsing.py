import io
import re
from typing import Iterable

import pdfplumber
from docx import Document

TECHNICAL_SKILLS = {
    "python", "java", "javascript", "typescript", "sql", "c++", "c#", "go", "rust",
    "fastapi", "django", "flask", "react", "node", "pytorch", "tensorflow", "scikit-learn",
    "machine learning", "deep learning", "nlp", "data analysis", "docker", "kubernetes",
}
SOFT_SKILLS = {
    "communication", "leadership", "teamwork", "problem solving", "critical thinking",
    "adaptability", "collaboration", "stakeholder management", "mentoring", "time management",
}
TOOLS = {
    "aws", "azure", "gcp", "git", "jira", "figma", "tableau", "power bi", "postgresql",
    "mysql", "mongodb", "linux", "airflow", "spark", "excel",
}
EDUCATION_KEYWORDS = ["bachelor", "master", "phd", "b.tech", "m.tech", "mba", "bs", "ms"]


def extract_text_from_file(filename: str, content: bytes) -> str:
    ext = filename.lower().split(".")[-1]
    if ext == "pdf":
        return _extract_pdf_text(content)
    if ext == "docx":
        return _extract_docx_text(content)
    raise ValueError("Unsupported file type. Please upload PDF or DOCX")


def _extract_pdf_text(content: bytes) -> str:
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        return "\n".join((page.extract_text() or "") for page in pdf.pages)


def _extract_docx_text(content: bytes) -> str:
    doc = Document(io.BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def find_keywords(text: str, vocabulary: Iterable[str]) -> list[str]:
    normalized = normalize_text(text)
    return sorted([kw for kw in vocabulary if kw in normalized])


def extract_years_of_experience(text: str) -> float:
    pattern = re.compile(r"(\d{1,2})\+?\s*(?:years|yrs)", re.IGNORECASE)
    years = [int(m.group(1)) for m in pattern.finditer(text)]
    return float(max(years) if years else 0.0)


def extract_education(text: str) -> str:
    normalized = normalize_text(text)
    for keyword in EDUCATION_KEYWORDS:
        if keyword in normalized:
            return keyword.upper()
    return "Not specified"
