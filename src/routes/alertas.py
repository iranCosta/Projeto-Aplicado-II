from fastapi import APIRouter, Path, Query

from src.controllers.alertas_controller import listar_alertas, reconhecer_alerta

router = APIRouter(prefix="/api/alertas", tags=["alertas"])


@router.get("", summary="Alertas (o status de um sensor piorou), do mais recente para o mais antigo")
def listar(limite: int = Query(50, ge=1, le=500),
           sensor_id: int | None = Query(None, gt=0),
           reconhecido: bool | None = Query(None, description="true/false; vazio traz todos")):
    return listar_alertas(limite, sensor_id, reconhecido)


@router.post("/{alerta_id}/reconhecer", summary="Marca o alerta como reconhecido pelo operador",
             responses={404: {"description": "Alerta não encontrado"}})
def reconhecer(alerta_id: int = Path(gt=0)):
    return reconhecer_alerta(alerta_id)
