from typing import Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from src.controllers.dados_controller import criar_leitura, listar_exemplo

router = APIRouter(prefix="/api", tags=["dados"])


class LeituraIn(BaseModel):
    sensor_id: int
    timestamp: str
    rms: float = Field(ge=0)
    assimetria: float
    curtose: float
    frequencia_pico: float = Field(ge=0)
    rotacao_rpm: float
    status_alerta: Literal["NORMAL", "ATENCAO", "CRITICO"]


@router.get("/exemplo")
def exemplo(limite: int = Query(10, ge=1, le=100)):
    return listar_exemplo(limite)


@router.post("/dados", status_code=201)
def criar(leitura: LeituraIn):
    return criar_leitura(leitura.model_dump())
