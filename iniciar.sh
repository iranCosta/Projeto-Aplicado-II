#!/usr/bin/env bash
# Início da API em servidor (Render e similares). Rode da raiz do projeto: bash iniciar.sh
# - gera os dados simulados e treina o modelo se ainda não existirem (não são versionados);
# - opcional: mantém um simulador enviando leituras novas, para o painel ficar "vivo" na demonstração.
#
# Variáveis: PORT (padrão 8000) · SIMULAR=1|0 (padrão 1) · SIM_INTERVALO (s entre rodadas, padrão 10)
#            SIM_ANOMALIAS (fração de anomalias, padrão 0.15)
set -euo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-8000}"
PY="${PYTHON:-python}"

if [ ! -f mock/data/vibracao.db ]; then
  echo "[iniciar] gerando dados simulados..."
  (cd mock && "$PY" simulator.py)
fi

if [ ! -f modelos_treinados/isolation_forest.joblib ]; then
  echo "[iniciar] treinando o modelo..."
  "$PY" -m services.modelo
fi

if [ "${SIMULAR:-1}" = "1" ]; then
  # espera a API subir; o simulador também tenta de novo sozinho se a API ainda não respondeu
  (
    sleep 12
    cd mock
    exec "$PY" simulator.py --modo stream --n 0 \
      --intervalo "${SIM_INTERVALO:-10}" --anomalias "${SIM_ANOMALIAS:-0.15}" \
      --api "http://127.0.0.1:${PORT}"
  ) &
fi

echo "[iniciar] subindo a API na porta ${PORT}"
exec "$PY" -m uvicorn src.main:app --host 0.0.0.0 --port "${PORT}"
