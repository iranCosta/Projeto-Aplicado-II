import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

PORT = int(os.getenv("PORT", "8000"))
DATABASE_PATH = (ROOT / os.getenv("DATABASE_PATH", "mock/data/vibracao.db")).resolve()
SCHEMA_PATH = (ROOT / os.getenv("SCHEMA_PATH", "mock/schema.sql")).resolve()
MODELO_PATH = (ROOT / os.getenv("MODELO_PATH", "modelos_treinados/isolation_forest.joblib")).resolve()
# origens que o navegador pode usar para chamar a API (painel Streamlit e fronts locais comuns)
CORS_ORIGINS = [o.strip() for o in os.getenv(
    "CORS_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501,http://localhost:3000,http://localhost:5173").split(",") if o.strip()]
# opcional: expressão regular para origens variáveis (ex.: previews da Vercel). Vazio = desligado
CORS_ORIGIN_REGEX = os.getenv("CORS_ORIGIN_REGEX", "").strip() or None
