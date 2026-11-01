from typing import Literal

from fastapi import APIRouter, Query

from src.controllers.dados_controller import criar_leitura, listar_diagnosticos, listar_exemplo, status_por_sensor
from src.schemas import LeituraIn

router = APIRouter(prefix="/api", tags=["dados"])

RESPOSTA_422 = {422: {"description": "Dados inválidos ou regra violada (ex.: sensor inexistente)"}}


@router.get("/exemplo")
def exemplo(limite: int = Query(10, ge=1, le=100)):
    return listar_exemplo(limite)


@router.post("/dados", status_code=201, responses=RESPOSTA_422,
             summary="Recebe uma leitura, aplica a regra de diagnóstico e grava")
def criar(leitura: LeituraIn):
    return criar_leitura(leitura.para_banco())


@router.get("/diagnosticos", summary="Leituras mais recentes com status, cor e motivos")
def diagnosticos(limite: int = Query(10, ge=1, le=500),
                 sensor_id: int | None = Query(None, gt=0),
                 status: Literal["NORMAL", "ATENCAO", "CRITICO"] | None = None):
    return listar_diagnosticos(limite, sensor_id, status)


@router.get("/status", summary="Status atual (última leitura) de cada sensor")
def status():
    return status_por_sensor()
