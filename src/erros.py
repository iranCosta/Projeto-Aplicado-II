"""
Tratamento de erros da API: respostas em português e sempre no mesmo formato,
{"detail": [{"campo": ..., "mensagem": ..., "recebido": ...}]}.
"""
import json
import sqlite3

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from services.regras import DadosInvalidosError

EXEMPLO_DATA = "2026-10-22T20:00:00Z"

MENSAGENS = {
    "missing": "campo obrigatório",
    "extra_forbidden": "campo não permitido",
    "int_type": "deve ser um número inteiro",
    "float_type": "deve ser um número",
    "finite_number": "deve ser um número finito (NaN e infinito não são aceitos)",
    "greater_than": "deve ser maior que {gt}",
    "greater_than_equal": "deve ser maior ou igual a {ge}",
    "less_than": "deve ser menor que {lt}",
    "less_than_equal": "deve ser menor ou igual a {le}",
    "timezone_aware": f"deve informar o fuso horário (ex.: {EXEMPLO_DATA})",
    "datetime_type": f"deve ser data e hora no formato ISO 8601 (ex.: {EXEMPLO_DATA})",
    "datetime_parsing": f"deve ser data e hora no formato ISO 8601 (ex.: {EXEMPLO_DATA})",
    "datetime_from_date_parsing": f"deve ser data e hora no formato ISO 8601 (ex.: {EXEMPLO_DATA})",
    "literal_error": "deve ser um destes valores: {expected}",
    "model_attributes_type": "o corpo da requisição deve ser um objeto JSON",
    "json_invalid": "JSON inválido",
}


def _json_seguro(valor):
    """NaN e infinito não existem em JSON: devolve como texto."""
    try:
        json.dumps(valor, allow_nan=False)
        return valor
    except (TypeError, ValueError):
        return repr(valor)


def _traduzir(erro: dict) -> dict:
    loc = [p for p in erro["loc"] if p not in ("body", "query", "path")]
    campo = ".".join(str(p) for p in loc) or None
    tipo, ctx = erro["type"], erro.get("ctx", {})

    if tipo == "value_error":  # validadores próprios (ex.: timestamp no futuro)
        mensagem = str(ctx.get("error", erro["msg"]))
    elif tipo == "extra_forbidden" and campo == "status_alerta":
        mensagem = "não deve ser enviado: o status é calculado pela API a partir dos indicadores"
    elif tipo in MENSAGENS:
        mensagem = MENSAGENS[tipo].format(**ctx)
    else:
        mensagem = erro["msg"]

    item = {"campo": campo, "mensagem": mensagem}
    if tipo != "missing":
        item["recebido"] = _json_seguro(erro.get("input"))
    return item


def registrar(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def _validacao(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": [_traduzir(e) for e in exc.errors()]})

    @app.exception_handler(DadosInvalidosError)
    async def _regra(request: Request, exc: DadosInvalidosError):
        return JSONResponse(status_code=422, content={"detail": [{"campo": None, "mensagem": str(exc)}]})

    @app.exception_handler(sqlite3.Error)
    async def _banco(request: Request, exc: sqlite3.Error):
        return JSONResponse(status_code=503, content={"detail": [{"campo": None, "mensagem": "banco de dados indisponível"}]})
