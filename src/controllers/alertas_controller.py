from fastapi import HTTPException

from src.database import get_connection
from src.models import alerta


def listar_alertas(limite: int, sensor_id: int | None, reconhecido: bool | None) -> dict:
    con = get_connection()
    try:
        dados = alerta.listar(con, limite, sensor_id, reconhecido)
        return {"total": len(dados), "nao_reconhecidos": alerta.contar_nao_reconhecidos(con), "alertas": dados}
    finally:
        con.close()


def reconhecer_alerta(alerta_id: int) -> dict:
    """Marca o alerta como visto pelo operador. Repetir a chamada não muda nada (idempotente)."""
    con = get_connection()
    try:
        if alerta.buscar(con, alerta_id) is None:
            raise HTTPException(status_code=404, detail=[{"campo": "alerta_id", "mensagem": "alerta não encontrado"}])
        alerta.reconhecer(con, alerta_id)
        return alerta.buscar(con, alerta_id)
    finally:
        con.close()
