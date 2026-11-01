import sqlite3

from fastapi import HTTPException

from services.regras import diagnosticar_leitura
from src import ia
from src.database import get_connection
from src.models import leitura


def _com_diagnostico(linhas: list[dict]) -> list[dict]:
    """Acrescenta a cada leitura do banco: cor e motivos (regra de limiar) e a avaliação do modelo.
    O status (semáforo) continua sendo o da regra; o modelo é um indicador à parte."""
    resultado = []
    for linha, aval in zip(linhas, ia.avaliar(linhas)):
        if linha.get("rms") is None:  # sensor sem leituras
            resultado.append({**linha, "cor": None, "motivos": ["sem leituras"], "modelo": None})
            continue
        d = diagnosticar_leitura(linha)
        resultado.append({**linha, "cor": d["cor"], "motivos": d["motivos"], "modelo": aval})
    return resultado


def listar_exemplo(limite: int) -> dict:
    con = get_connection()
    try:
        dados = leitura.listar_ultimas(con, limite)
        return {"total": len(dados), "leituras": dados}
    finally:
        con.close()


def listar_diagnosticos(limite: int, sensor_id: int | None, status: str | None) -> dict:
    con = get_connection()
    try:
        dados = _com_diagnostico(leitura.listar_filtradas(con, limite, sensor_id, status))
        return {"total": len(dados), "diagnosticos": dados}
    finally:
        con.close()


def status_por_sensor() -> dict:
    con = get_connection()
    try:
        sensores = _com_diagnostico(leitura.ultima_por_sensor(con))
        return {"total": len(sensores), "sensores": sensores}
    finally:
        con.close()


def criar_leitura(dados: dict) -> dict:
    """Aplica a regra de negócio, grava a leitura com o status calculado e devolve o diagnóstico.
    DadosInvalidosError (ex.: sensor inexistente) vira 422 pelo handler em src/erros.py."""
    con = get_connection()
    try:
        diagnostico = diagnosticar_leitura(dados, sensores_validos=leitura.ids_sensores(con))
        registro = {**dados, "status_alerta": diagnostico["status"]}
        try:
            novo_id = leitura.inserir(con, registro)
        except sqlite3.IntegrityError as e:
            raise HTTPException(status_code=422, detail=[{"campo": None, "mensagem": f"rejeitado pelo banco: {e}"}])
        return {"id": novo_id, **registro, "cor": diagnostico["cor"], "motivos": diagnostico["motivos"],
                "modelo": ia.avaliar([registro])[0]}
    finally:
        con.close()
