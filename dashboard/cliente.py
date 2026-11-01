"""Cliente HTTP da API. O painel só lê dados por aqui (nunca acessa o banco diretamente)."""
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
# 127.0.0.1 e não "localhost": no Windows, "localhost" tenta IPv6 primeiro e custa ~2 s por chamada
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
TIMEOUT_S = 5


class ApiIndisponivel(Exception):
    """A API não respondeu ou devolveu erro."""


def _get(caminho: str, **params) -> dict:
    try:
        r = requests.get(f"{API_URL}{caminho}", params=params, timeout=TIMEOUT_S)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        raise ApiIndisponivel(f"{API_URL}{caminho}: {e}") from e


def status_sensores() -> list[dict]:
    """Última leitura de cada sensor, com status, cor e motivos."""
    return _get("/api/status")["sensores"]


def historico(sensor_id: int, limite: int = 200) -> list[dict]:
    """Leituras mais recentes de um sensor (da mais nova para a mais antiga)."""
    return _get("/api/diagnosticos", sensor_id=sensor_id, limite=limite)["diagnosticos"]


def alertas_pendentes(limite: int = 10) -> dict:
    """Alertas ainda não reconhecidos (mais recentes primeiro) e o total pendente."""
    return _get("/api/alertas", limite=limite, reconhecido="false")


def reconhecer(alerta_id: int) -> dict:
    try:
        r = requests.post(f"{API_URL}/api/alertas/{alerta_id}/reconhecer", timeout=TIMEOUT_S)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        raise ApiIndisponivel(f"{API_URL}/api/alertas/{alerta_id}/reconhecer: {e}") from e
