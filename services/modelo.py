"""
Detecção de anomalias com Isolation Forest (não supervisionado).

- Um modelo por sensor: cada máquina e posição tem o seu "normal".
- Features: só os indicadores da janela. anomalia_real e tipo_anomalia são o gabarito
  do simulador e NUNCA entram no treino (seria vazamento de dados); servem só para avaliar.
- Avaliação honesta: treino nos primeiros 70% das leituras de cada sensor (ordem temporal)
  e teste nos 30% finais, que o modelo não viu.
- O modelo é salvo com joblib e carregado pela API sem retreinar (RNF03).

Treinar (da raiz):  python -m services.modelo
"""
import argparse
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import IsolationForest

FEATURES = ["rms", "assimetria", "curtose", "frequencia_pico"]
FRACAO_TREINO = 0.7
CONTAMINACAO = 0.08  # fração esperada de leituras anômalas no treino
RAIZ = Path(__file__).resolve().parent.parent
BANCO_PADRAO = RAIZ / "mock" / "data" / "vibracao.db"
MODELO_PADRAO = RAIZ / "modelos_treinados" / "isolation_forest.joblib"


def ler_banco(caminho: Path) -> pd.DataFrame:
    with closing(sqlite3.connect(caminho)) as con:
        return pd.read_sql_query("SELECT * FROM leituras_brutas ORDER BY sensor_id, timestamp, id", con)


def separar_treino_teste(df: pd.DataFrame, fracao: float = FRACAO_TREINO) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Divisão temporal por sensor: o começo de cada série treina, o final testa."""
    treino, teste = [], []
    for _, g in df.sort_values(["sensor_id", "timestamp", "id"]).groupby("sensor_id"):
        corte = int(len(g) * fracao)
        treino.append(g.iloc[:corte])
        teste.append(g.iloc[corte:])
    return pd.concat(treino), pd.concat(teste)


def treinar(df: pd.DataFrame, contaminacao: float = CONTAMINACAO, seed: int = 42) -> dict[int, IsolationForest]:
    modelos = {}
    for sid, g in df.groupby("sensor_id"):
        m = IsolationForest(n_estimators=200, contamination=contaminacao, random_state=seed)
        modelos[int(sid)] = m.fit(g[FEATURES].to_numpy())
    return modelos


def pontuar(modelos: dict[int, IsolationForest], df: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta anomalia_if (0/1, ou nulo se o sensor não tem modelo) e score_if (maior = mais anômalo)."""
    # trabalha por posição (não pelo índice), para aceitar qualquer DataFrame, até com índice repetido
    sensores = df["sensor_id"].to_numpy()
    X = df[FEATURES].to_numpy(dtype=float)
    anomalia = pd.array([pd.NA] * len(df), dtype="Int64")
    score = np.full(len(df), np.nan)
    for sid in np.unique(sensores):
        m = modelos.get(int(sid))
        if m is None:
            continue
        pos = sensores == sid
        anomalia[pos] = (m.predict(X[pos]) == -1).astype(int)
        score[pos] = -m.score_samples(X[pos])
    return df.assign(anomalia_if=anomalia, score_if=score)


def metricas(real: pd.Series, previsto: pd.Series) -> dict:
    tp = int(((real == 1) & (previsto == 1)).sum())
    fp = int(((real == 0) & (previsto == 1)).sum())
    fn = int(((real == 1) & (previsto == 0)).sum())
    return {"detectadas": tp, "falsos_alarmes": fp, "perdidas": fn,
            "precisao": round(tp / (tp + fp), 3) if tp + fp else 0.0,
            "recall": round(tp / (tp + fn), 3) if tp + fn else 0.0}


def avaliar(modelos: dict, teste: pd.DataFrame) -> dict:
    """Compara modelo e regra de limiar contra o gabarito do simulador, só no conjunto de teste."""
    p = pontuar(modelos, teste)
    return {"leituras_teste": len(p), "anomalias_reais": int(p["anomalia_real"].sum()),
            "isolation_forest": metricas(p["anomalia_real"], p["anomalia_if"].astype(int)),
            "regra_de_limiar": metricas(p["anomalia_real"], (p["status_alerta"] != "NORMAL").astype(int))}


def salvar(modelos: dict, caminho: Path, info: dict) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"modelos": modelos, "features": FEATURES, "sklearn": sklearn.__version__, **info}, caminho, compress=3)


def carregar(caminho: Path = MODELO_PADRAO) -> dict | None:
    """Pacote salvo por salvar(), ou None se o arquivo não existir."""
    return joblib.load(caminho) if Path(caminho).exists() else None


def main(argv=None):
    p = argparse.ArgumentParser(description="Treina o Isolation Forest (um por sensor) e salva com joblib")
    p.add_argument("--banco", default=str(BANCO_PADRAO))
    p.add_argument("--saida", default=str(MODELO_PADRAO))
    p.add_argument("--contaminacao", type=float, default=CONTAMINACAO)
    args = p.parse_args(argv)

    df = ler_banco(Path(args.banco))
    treino, teste = separar_treino_teste(df)
    resultado = avaliar(treinar(treino, args.contaminacao), teste)

    # o modelo final usa todo o histórico; as métricas acima vêm do teste separado
    modelos = treinar(df, args.contaminacao)
    salvar(modelos, Path(args.saida), {"treinado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                        "leituras_treino": len(df), "contaminacao": args.contaminacao,
                                        "avaliacao": resultado})

    print(f"[ok] {len(modelos)} modelos (um por sensor) salvos em {args.saida}")
    print(f"Avaliação no teste ({resultado['leituras_teste']} leituras, "
          f"{resultado['anomalias_reais']} anomalias reais, últimos {1 - FRACAO_TREINO:.0%} de cada sensor):")
    for nome in ("isolation_forest", "regra_de_limiar"):
        print(f"  {nome:17} {resultado[nome]}")
    return resultado


if __name__ == "__main__":
    main()
