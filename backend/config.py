"""
Application Configuration and Environment Loader
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Find and load .env file from project root
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

CRUSTDATA_API_KEY = os.getenv("CRUSTDATA_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./founder_box.db")
MAX_DAILY_CRUSTDATA_CREDITS = int(os.getenv("MAX_DAILY_CRUSTDATA_CREDITS", 500))
ENABLE_HITL_APPROVAL = os.getenv("ENABLE_HITL_APPROVAL", "True").lower() in ("true", "1", "t")

