import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

PORT = int(os.getenv("PORT", "8000"))
DATABASE_PATH = (ROOT / os.getenv("DATABASE_PATH", "mock/data/vibracao.db")).resolve()
SCHEMA_PATH = (ROOT / os.getenv("SCHEMA_PATH", "mock/schema.sql")).resolve()
