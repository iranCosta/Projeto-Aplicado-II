from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.config import PORT
from src.database import init_db
from src.routes import dados, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # cria as tabelas automaticamente na inicialização
    yield


app = FastAPI(title="Diagnóstico Preditivo - API", lifespan=lifespan)
app.include_router(health.router)
app.include_router(dados.router)

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=PORT, reload=True)
