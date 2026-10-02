#!/usr/bin/env python3
"""
Leitura, validação e teste dos dados de vibração (camada de ingestão do MVP).

Lê SQLite, CSV ou JSON gerados pelo simulator.py, valida cada linha (separando
as inválidas), calcula um resumo por sensor e, opcionalmente, roda o Isolation
Forest e compara com o gabarito do mock.

Uso:
    python leitor_dados.py                          # lê data/vibracao.db e mostra resumo
    python leitor_dados.py --fonte csv              # lê data/leituras_brutas.csv
    python leitor_dados.py --fonte json
    python leitor_dados.py --detectar               # + Isolation Forest vs. gabarito
    python leitor_dados.py --arquivo meu.csv        # arquivo próprio (mesmas colunas)

Como módulo (no dashboard / pipeline):
    from leitor_dados import carregar, validar
    df = carregar("sqlite")
    ok, rejeitadas = validar(df)
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent / "data"
COLUNAS_OBRIGATORIAS = ["sensor_id", "timestamp", "rms", "assimetria", "curtose",
                        "frequencia_pico", "rotacao_rpm", "status_alerta"]
FEATURES = ["rms", "assimetria", "curtose", "frequencia_pico"]
STATUS_VALIDOS = {"NORMAL", "ATENCAO", "CRITICO"}


# ------------------------------------------------------------------ leitura
def carregar(fonte: str = "sqlite", arquivo: str | None = None) -> pd.DataFrame:
    """Retorna DataFrame com as leituras, na mesma estrutura para qualquer fonte."""
    if fonte == "sqlite":
        caminho = Path(arquivo) if arquivo else DATA / "vibracao.db"
        with sqlite3.connect(caminho) as con:
            df = pd.read_sql_query(
                "SELECT l.*, s.ativo_id, a.tag FROM leituras_brutas l "
                "JOIN sensores s ON s.id = l.sensor_id JOIN ativos a ON a.id = s.ativo_id "
                "ORDER BY l.timestamp, l.sensor_id", con)
    elif fonte == "csv":
        df = pd.read_csv(arquivo or DATA / "leituras_brutas.csv")
    elif fonte == "json":
        doc = json.loads(Path(arquivo or DATA / "leituras_brutas.json").read_text(encoding="utf-8"))
        df = pd.DataFrame(doc["leituras_brutas"] if isinstance(doc, dict) else doc)
    else:
        raise ValueError(f"fonte desconhecida: {fonte}")
    return df


# ------------------------------------------------------------------ validação
def validar(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separa linhas válidas das rejeitadas (com coluna 'motivo'). Nunca derruba o pipeline."""
    faltando = [c for c in COLUNAS_OBRIGATORIAS if c not in df.columns]
    if faltando:
        raise ValueError(f"colunas ausentes: {faltando}")

    d = df.copy()
    d["timestamp"] = pd.to_datetime(d["timestamp"], errors="coerce", utc=True)
    for c in FEATURES + ["rotacao_rpm"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")

    regras = {
        "timestamp inválido": d["timestamp"].isna(),
        "valor nulo/não numérico": d[FEATURES + ["rotacao_rpm"]].isna().any(axis=1),
        "rms negativo": d["rms"] < 0,
        "frequência de pico negativa": d["frequencia_pico"] < 0,
        "status desconhecido": ~d["status_alerta"].isin(STATUS_VALIDOS),
        "duplicada (sensor+timestamp)": d.duplicated(["sensor_id", "timestamp"], keep="first"),
    }
    motivo = pd.Series("", index=d.index)
    for nome, mask in regras.items():
        motivo = motivo.where(~(mask & (motivo == "")), nome)
    invalida = motivo != ""
    rejeitadas = d[invalida].assign(motivo=motivo[invalida])
    return d[~invalida].reset_index(drop=True), rejeitadas.reset_index(drop=True)


# ------------------------------------------------------------------ análise
def resumo_por_sensor(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("sensor_id")
    out = g.agg(leituras=("rms", "size"), rms_medio=("rms", "mean"), rms_max=("rms", "max"),
                curtose_max=("curtose", "max"))
    for st in ["NORMAL", "ATENCAO", "CRITICO"]:
        out[st] = g["status_alerta"].apply(lambda s, st=st: (s == st).sum())
    return out.round(2)


def detectar_isolation_forest(df: pd.DataFrame, contaminacao: float = 0.08, seed: int = 42) -> pd.DataFrame:
    """Treina um Isolation Forest por sensor (cada máquina tem seu 'normal') e marca anomalias."""
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler

    partes = []
    for _, grupo in df.groupby("sensor_id"):
        X = StandardScaler().fit_transform(grupo[FEATURES])
        modelo = IsolationForest(n_estimators=200, contamination=contaminacao, random_state=seed)
        pred = modelo.fit_predict(X)
        partes.append(grupo.assign(anomalia_if=(pred == -1).astype(int),
                                   score_if=-modelo.score_samples(X)))
    return pd.concat(partes).sort_index()


def avaliar_contra_gabarito(df: pd.DataFrame) -> dict:
    """Só funciona com dados do mock (coluna anomalia_real)."""
    real, prev, regra = df["anomalia_real"], df["anomalia_if"], (df["status_alerta"] != "NORMAL").astype(int)

    def m(p):
        tp = int(((real == 1) & (p == 1)).sum()); fp = int(((real == 0) & (p == 1)).sum())
        fn = int(((real == 1) & (p == 0)).sum())
        return {"detectadas": tp, "falsos_alarmes": fp, "perdidas": fn,
                "precisao": round(tp / (tp + fp), 3) if tp + fp else 0.0,
                "recall": round(tp / (tp + fn), 3) if tp + fn else 0.0}
    return {"isolation_forest": m(prev), "regra_de_limiar": m(regra)}


# ------------------------------------------------------------------ CLI
def main(argv=None):
    p = argparse.ArgumentParser(description="Leitura e teste dos dados de vibração")
    p.add_argument("--fonte", choices=["sqlite", "csv", "json"], default="sqlite")
    p.add_argument("--arquivo", help="caminho de um arquivo próprio")
    p.add_argument("--detectar", action="store_true", help="roda o Isolation Forest e compara com o gabarito")
    p.add_argument("--contaminacao", type=float, default=0.08)
    args = p.parse_args(argv)

    try:
        df = carregar(args.fonte, args.arquivo)
    except (FileNotFoundError, sqlite3.Error) as e:
        sys.exit(f"Não consegui ler os dados ({e}). Rode antes: python simulator.py")
    print(f"[leitura] fonte={args.fonte} linhas={len(df)}")

    ok, rej = validar(df)
    print(f"[validação] válidas={len(ok)} rejeitadas={len(rej)}")
    if len(rej):
        print(rej["motivo"].value_counts().to_string())

    print("\n== Resumo por sensor ==")
    print(resumo_por_sensor(ok).to_string())

    if args.detectar:
        res = detectar_isolation_forest(ok, args.contaminacao)
        print("\n== Isolation Forest x regra de limiar (vs. gabarito do mock) ==")
        if "anomalia_real" in res.columns:
            for nome, met in avaliar_contra_gabarito(res).items():
                print(f"  {nome:17s} {met}")
        top = res.sort_values("score_if", ascending=False).head(5)
        print("\n== 5 leituras mais anômalas ==")
        print(top[["timestamp", "sensor_id", "rms", "curtose", "frequencia_pico", "score_if"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
