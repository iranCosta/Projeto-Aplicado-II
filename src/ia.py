"""
Isolation Forest carregado uma vez na inicialização da API (sem retreinar a cada requisição).
Se o arquivo do modelo não existir, a API continua funcionando só com a regra de limiar.
"""
import pandas as pd

from services import modelo
from src.config import MODELO_PATH

_pacote: dict | None = None


def carregar() -> None:
    global _pacote
    _pacote = modelo.carregar(MODELO_PATH)


def info() -> dict:
    if _pacote is None:
        return {"carregado": False}
    return {"carregado": True, "treinado_em": _pacote.get("treinado_em"), "sensores": sorted(_pacote["modelos"])}


def avaliar(linhas: list[dict]) -> list[dict | None]:
    """Para cada leitura: {"anomalia": bool, "score": float}, ou None se não houver modelo para ela."""
    resultado: list[dict | None] = [None] * len(linhas)
    indices = [i for i, l in enumerate(linhas) if l.get("rms") is not None]
    if _pacote is None or not indices:
        return resultado
    df = pd.DataFrame([{"sensor_id": linhas[i]["sensor_id"], **{f: linhas[i][f] for f in modelo.FEATURES}}
                       for i in indices], index=indices)
    df = modelo.pontuar(_pacote["modelos"], df)
    for i, anomalia, score in zip(df.index, df["anomalia_if"], df["score_if"]):
        if not pd.isna(anomalia):
            resultado[i] = {"anomalia": bool(anomalia), "score": round(float(score), 3)}
    return resultado
