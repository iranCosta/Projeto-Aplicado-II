# /mock — Dados e Mocks Industriais (Aula 03)

Modelagem + gerador de dados de vibração para ArcelorMittal / Tuper.

## Modelagem (`schema.sql`, SQLite, 4 tabelas)
| Tabela | Conteúdo |
|---|---|
| `ativos` | motores e compressores (tag, tipo, rpm nominal) |
| `sensores` | sensores de vibração por ativo (posição, taxa de amostragem) |
| `leituras_brutas` | timestamp, sensor_id, rms, assimetria, curtose, frequencia_pico, rotacao_rpm, status_alerta (+ gabarito `anomalia_real`/`tipo_anomalia`) |
| `alertas` | gerado quando o status de um sensor piora (NORMAL → ATENCAO → CRITICO) |

> As colunas `anomalia_real` e `tipo_anomalia` existem só no mock, para medir o detector (Isolation Forest). Não use como feature.

## Como rodar
```bash
pip install -r mock/requirements.txt
cd mock
python simulator.py                          # lote de 3000 leituras -> data/vibracao.db
python simulator.py --n 5000 --saida sqlite csv json
python simulator.py --modo stream --intervalo 1      # tempo real, Ctrl+C para parar
python validar.py                            # relatório + verificações
python -m unittest test_mock -v              # testes automatizados
```
Opções: `--anomalias 0.10` (fração de anomalias), `--seed 42` (reprodutível), `--passo 60` (s entre leituras), `--pasta`.

## Comportamento simulado
Cada leitura é uma janela de 1024 amostras a 2048 Hz (sinal 1x + 2x da rotação + ruído) reduzida a RMS, assimetria, curtose e frequência de pico. ~90% normal, ~10% em episódios de anomalia com severidade crescente:
`DESBALANCEAMENTO` (RMS sobe), `DESALINHAMENTO` (2x forte), `FALHA_ROLAMENTO` (impulsos → curtose alta), `PICO_ISOLADO` (curtose extrema), `SENSOR_TRAVADO` (RMS ≈ 0).

Limiares de status (ISO 10816 adaptado): RMS ≥ 4,5 ou curtose ≥ 4 → ATENCAO; RMS ≥ 7,1 ou curtose ≥ 8 → CRITICO.

## Leitura e teste dos dados (`leitor_dados.py`)
```bash
pip install -r requirements.txt
python leitor_dados.py                  # lê data/vibracao.db, valida e resume por sensor
python leitor_dados.py --fonte csv      # ou json / --arquivo caminho
python leitor_dados.py --detectar       # + Isolation Forest vs. regra de limiar (usa o gabarito do mock)
python -m unittest test_leitor -v       # testes da leitura/validação
```
No código do pipeline/dashboard: `from leitor_dados import carregar, validar` → `ok, rejeitadas = validar(carregar("sqlite"))`.
Linhas inválidas (nulo, RMS negativo, status desconhecido, timestamp ruim, duplicada) vão para `rejeitadas` com o motivo, sem derrubar a leitura.
