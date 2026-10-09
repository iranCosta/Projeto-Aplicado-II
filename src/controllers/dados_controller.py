import sqlite3

from fastapi import HTTPException

from src.database import get_connection
from src.models import leitura


def listar_exemplo(limite: int) -> dict:
    con = get_connection()
    try:
        dados = leitura.listar_ultimas(con, limite)
        return {"total": len(dados), "leituras": dados}
    finally:
        con.close()


def criar_leitura(dados: dict) -> dict:
    con = get_connection()
    try:
        try:
            novo_id = leitura.inserir(con, dados)
        except sqlite3.IntegrityError as e:
            raise HTTPException(status_code=422, detail=f"Rejeitado pelo banco: {e}")
        return {"id": novo_id, **dados}
    finally:
        con.close()
