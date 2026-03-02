import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

BACKEND_DIR = Path(__file__).resolve().parent

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(BACKEND_DIR / "grc_learning.db")))
VIDEO_DATA_DIR = Path(os.getenv("VIDEO_DATA_DIR", str(PROJECT_ROOT / "video_data")))
PROCESSED_DIR = VIDEO_DATA_DIR / "processed"
APPROVED_WORKFLOWS_DIR = Path(os.getenv("APPROVED_WORKFLOWS_DIR", str(PROJECT_ROOT / "approved_workflows")))

FRAME_INTERVAL_SECONDS = 3
LLM_MODEL = "gemini-2.5-flash"
GEMINI_MODEL = "gemini-2.5-flash"
MAX_SESSION_HISTORY = 5
