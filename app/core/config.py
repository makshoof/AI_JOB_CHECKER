from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "ai_job_match.db"
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
