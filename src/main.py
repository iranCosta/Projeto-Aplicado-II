from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src import erros, ia
from src.config import PORT
from src.database import init_db
from src.routes import alertas, dados, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # cria as tabelas automaticamente na inicialização
    ia.carregar()  # Isolation Forest salvo com joblib (se existir)
    yield


app = FastAPI(title="Diagnóstico Preditivo - API", lifespan=lifespan)
erros.registrar(app)
app.include_router(health.router)
app.include_router(dados.router)
app.include_router(alertas.router)

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=PORT, reload=True)
