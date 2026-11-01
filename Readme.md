# 🛠️ Sistema Inteligente de Diagnóstico Preditivo de Falhas Mecânicas

> **Empresa:** ArcelorMittal / Tuper

---

## Equipe

- **Ederlane Ciribelle Silva Fernandes**
- **Iran Andrei da Costa**
- **Paulo Ricardo Wosniak Soares**

---

## Visão Geral

O **Sistema Inteligente de Diagnóstico Preditivo** é uma solução voltada para a indústria com o objetivo de otimizar rotinas de manutenção preditiva e evitar paradas não planejadas em linhas de produção.

O sistema recebe dados de vibração e rotação de máquinas industriais (motores e compressores), calcula indicadores estatísticos e aplica regras e Inteligência Artificial para identificar comportamentos anômalos que indicam desgaste mecânico ou iminência de falha. Os resultados são exibidos em um painel web com status por cores.

> No MVP os dados são **sintéticos**, gerados por um simulador (`mock/`), e o painel é atualizado a partir do banco de dados (não há conexão direta com os sensores da planta).

## Objetivo Geral

Desenvolver uma aplicação capaz de analisar dados de sensores de vibração, detectar anomalias em equipamentos industriais e emitir alertas preditivos categorizados (🟢 Normal, 🟡 Atenção, 🔴 Crítico), auxiliando na redução de custos e na prevenção de falhas graves em componentes mecânicos.

---

## Status do Projeto

| Componente | Status | Onde |
|---|---|---|
| Simulador de dados de vibração (lote e *stream*) | ✅ Pronto | `mock/simulator.py` |
| Modelagem do banco (SQLite, 4 tabelas) | ✅ Pronto | `mock/schema.sql` |
| Leitura e validação dos dados (SQLite/CSV/JSON) | ✅ Pronto | `mock/leitor_dados.py` |
| API FastAPI (`/health`, `POST /api/dados`, `/api/diagnosticos`, `/api/status`) | ✅ Pronto e testado | `src/` |
| Regra de diagnóstico por limiar (ISO 10816 adaptada) | ✅ Pronto e testado (chamado pelo `POST /api/dados`) | `services/regras.py` |
| Detecção de anomalias com Isolation Forest (um modelo por sensor) | ✅ Pronto e testado (na API e no painel) | `services/modelo.py`, `src/ia.py` |
| Salvar/carregar o modelo treinado (`joblib`) | ✅ Pronto (gerado localmente, não versionado) | `modelos_treinados/` |
| Dashboard web (Streamlit): cartões de status, alertas, gráfico de RMS/curtose e diagnóstico | ✅ Pronto | `dashboard/` |

---

## Arquitetura

```mermaid
flowchart LR
    A["Fontes de dados<br/>simulador · CSV · JSON<br/>POST /api/dados"] --> B["Ingestão e validação<br/>leitor_dados.py"]
    B --> C[("SQLite<br/>leituras_brutas")]
    C --> D["Indicadores por janela<br/>RMS · assimetria · curtose<br/>freq. de pico · rpm"]
    D --> E["Regra por limiar<br/>services/regras.py"]
    D --> F["Isolation Forest<br/>services/modelo.py"]
    E -->|"status piorou"| G[("Tabela alertas")]
    F -->|"anomalia + score"| H
    G --> H["API FastAPI<br/>src/"]
    C --> H
    H --> I["Dashboard Streamlit<br/>dashboard/"]
```

**Fluxo:** ingestão → indicadores → detecção (regra + Isolation Forest) → alertas → API → dashboard.

Cada linha de `leituras_brutas` representa **uma janela de vibração já reduzida a indicadores** (RMS, assimetria, curtose, frequência de pico). O simulador usa janelas de 1024 amostras a 2048 Hz.

**Camadas da API** (`src/`): `routes` (HTTP e validação Pydantic) → `controllers` (regras de aplicação) → `models` (consultas SQL) → `database` (conexão SQLite).

---

## Stack

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.10 ou mais novo (testado com 3.12 e 3.13) |
| Backend / API | FastAPI + Uvicorn |
| Banco de dados | SQLite |
| Análise e ML | pandas, NumPy, scikit-learn (`IsolationForest`) |
| Persistência do modelo | `joblib` (arquivo `.joblib` em `modelos_treinados/`) |
| **Interface** | **Streamlit consumindo a API FastAPI via HTTP** |
| Testes | `unittest` |

> A interface foi definida como **Streamlit**: ele lê os dados pela API (`/api/...`) em vez de acessar o banco diretamente, mantendo o backend como única porta de entrada.

---

## Estrutura de Pastas

```
.
├── Readme.md
├── AI_LOG.md                  # histórico do uso de IA no projeto
├── docs/
│   ├── prompt_continuidade.md # prompt usado para retomar o projeto em outra sessão de IA
│   └── roteiro_demonstracao.md # roteiro da demonstração ao vivo (Checkpoint 2)
├── requirements.txt           # dependências da API e do ML
├── .env.example               # modelo de configuração (copiar para .env)
├── .gitignore
├── src/                       # API FastAPI
│   ├── main.py                # cria o app, inicializa o banco e registra as rotas
│   ├── schemas.py             # validação da entrada (Pydantic): tipos e limites operacionais
│   ├── erros.py               # respostas de erro em português (422 e 503)
│   ├── ia.py                  # carrega o modelo na inicialização e avalia as leituras
│   ├── test_api.py            # testes da API
│   ├── config.py              # lê o .env (PORT, DATABASE_PATH, SCHEMA_PATH)
│   ├── database.py            # conexão SQLite, init_db(), ativos e sensores iniciais
│   ├── routes/                # health.py, dados.py, alertas.py
│   ├── controllers/           # health_controller.py, dados_controller.py, alertas_controller.py
│   └── models/                # leitura.py, alerta.py (consultas SQL)
├── services/
│   ├── regras.py              # diagnóstico por limiar (NORMAL / ATENCAO / CRITICO)
│   ├── modelo.py              # Isolation Forest: treino, avaliação, joblib
│   ├── test_regras.py         # testes da regra
│   └── test_modelo.py         # testes do modelo
├── mock/                      # dados e simulador (ver mock/README.md)
│   ├── schema.sql             # modelagem do banco
│   ├── simulator.py           # gerador de leituras de vibração
│   ├── leitor_dados.py        # leitura e validação dos dados
│   ├── validar.py             # relatório de verificação
│   ├── test_mock.py
│   ├── test_leitor.py
│   ├── requirements.txt
│   └── data/                  # ativos.csv, sensores.csv, leituras_brutas.csv/.json
│                              # vibracao.db é gerado localmente (não versionado)
├── dashboard/                 # painel Streamlit (lê os dados só pela API)
│   ├── app.py                 # cartões por sensor, gráfico e diagnóstico
│   ├── cliente.py             # chamadas HTTP à API (API_URL)
│   └── test_dashboard.py      # testes do painel com a API simulada
└── modelos_treinados/         # modelo salvo por `python -m services.modelo` (não versionado)
```

---

## Como Rodar

**Pré-requisito:** Python 3.10 ou mais novo, com `pip` (o código usa anotações como `str | None`). No Windows, clone numa pasta de caminho curto (ex.: `Downloads`): caminhos longos passam do limite de 260 caracteres e quebram a criação do `venv`.

```bash
# 1. clonar
git clone https://github.com/iranCosta/Projeto-Aplicado-II.git
cd Projeto-Aplicado-II

# 2. ambiente virtual
python -m venv venv
source venv/bin/activate          # Linux/macOS
# venv\Scripts\Activate.ps1       # Windows (PowerShell)
# source venv/Scripts/activate     # Windows (Git Bash)

# 3. dependências
pip install -r requirements.txt

# 4. configuração (opcional: já existem valores padrão)
cp .env.example .env              # Windows: copy .env.example .env
```

**Gerar os dados de teste** (cria `mock/data/vibracao.db`):

```bash
cd mock
python simulator.py               # 3000 leituras, semente 42 (reprodutível)
cd ..
```

**Treinar o modelo** (cria `modelos_treinados/isolation_forest.joblib`; sem ele, a API funciona só com a regra):

```bash
python -m services.modelo
```

O treino separa as leituras de cada sensor no tempo: os primeiros 70% treinam e os 30% finais avaliam, comparando com o gabarito do simulador. Resultado com a semente 42 (900 leituras de teste, 50 anomalias reais):

| Detector | Detectadas | Perdidas | Falsos alarmes | Precisão | Recall |
|---|---|---|---|---|---|
| Isolation Forest | 47 | 3 | 14 | 0,77 | 0,94 |
| Regra de limiar | 31 | 19 | 0 | 1,00 | 0,62 |

O modelo salvo é treinado depois com todo o histórico. `anomalia_real` e `tipo_anomalia` nunca entram como feature.

**Subir a API** (a partir da raiz do projeto):

```bash
uvicorn src.main:app --reload
```

A API fica em `http://localhost:8000` e a documentação interativa em `http://localhost:8000/docs`. Se o banco ainda não existir, as tabelas são criadas automaticamente na inicialização (sem leituras).

**Testar:**

```bash
curl http://localhost:8000/health
curl "http://localhost:8000/api/diagnosticos?limite=5"
curl http://localhost:8000/api/status
```

**Subir o painel** (em outro terminal, com a API no ar):

```bash
streamlit run dashboard/app.py
```

O painel abre em `http://localhost:8501` e se atualiza a cada 10 s. Ele mostra quando está carregando, a hora da última atualização e, se a API cair, mantém os últimos dados na tela (esmaecidos) com um aviso vermelho de desde quando está sem comunicação. O endereço da API vem de `API_URL` no `.env` (padrão `http://127.0.0.1:8000`; no Windows, `localhost` custa ~2 s por chamada porque tenta IPv6 antes).

**Fluxo ponta a ponta** (simulador → API → painel): com a API e o painel no ar, deixe o simulador rodando em outro terminal, enviando cada leitura pelo `POST /api/dados`:

```bash
cd mock
python simulator.py --modo stream --n 0 --intervalo 1 --api http://127.0.0.1:8000
```

A API diagnostica, grava, gera alertas e avalia com o modelo; o terminal mostra o status devolvido, os alertas e os avisos do modelo, e o painel reage a cada 10 s. Para a demonstração, `--anomalias 0.3` faz os eventos aparecerem mais rápido. Use a mesma `--seed` do lote usado no treino (padrão 42): a semente define o "normal" de cada sensor, e com outra semente o modelo estranha máquinas sãs. Se a API cair, o simulador avisa e tenta de novo na rodada seguinte. Sem `--api`, o modo contínuo grava direto no banco (sem passar pelo backend).

**CORS:** a API libera as origens listadas em `CORS_ORIGINS` no `.env` (padrão: o painel em `:8501` e fronts locais em `:3000` e `:5173`), com os métodos `GET` e `POST`. O painel Streamlit chama a API pelo servidor Python e não depende disso; a configuração vale para qualquer front que rode no navegador.

**Rodar os testes automatizados:**

```bash
python -m unittest services.test_regras services.test_modelo src.test_api dashboard.test_dashboard -v     # regra, modelo, API e painel (na raiz)
cd mock
python -m unittest test_mock test_leitor -v
```

**Demonstração da regra no terminal** (caso perfeito, crítico e erro de entrada):

```bash
python -m services.regras
```

### Endpoints

| Método | Rota | Descrição | Respostas |
|---|---|---|---|
| GET | `/health` | Verifica a conexão com o banco e informa se o modelo está carregado | `200` saudável · `503` banco indisponível |
| POST | `/api/dados` | Valida a leitura, aplica a regra de diagnóstico e grava com o status calculado | `201` criada · `422` dados inválidos ou sensor inexistente · `503` banco indisponível |
| GET | `/api/diagnosticos?limite=10&sensor_id=&status=` | Últimas leituras com status, cor e motivos (filtros opcionais) | `200` · `422` filtro inválido |
| GET | `/api/status` | Status atual (última leitura) de cada sensor | `200` |
| GET | `/api/alertas?limite=50&sensor_id=&reconhecido=` | Alertas (o status de um sensor piorou), com o total não reconhecido | `200` · `422` filtro inválido |
| POST | `/api/alertas/{id}/reconhecer` | Marca o alerta como reconhecido pelo operador (pode repetir) | `200` · `404` não encontrado |

Exemplo de corpo do `POST /api/dados`:

```json
{
  "sensor_id": 1,
  "timestamp": "2026-10-22T20:00:00Z",
  "rms": 1.53,
  "assimetria": 0.18,
  "curtose": 3.0,
  "frequencia_pico": 30.0,
  "rotacao_rpm": 1780
}
```

O `status_alerta` **não é enviado**: a API calcula com `services/regras.py` e devolve junto com `cor` e `motivos`. Se o status do sensor piorou em relação à leitura anterior (no tempo), o `POST` também grava um alerta (RF05) e devolve `alerta`: `{"id": 29, "severidade": "CRITICO"}` (ou `null`). As respostas de leitura também trazem `modelo`: `{"anomalia": true, "score": 0.73}` (score maior = mais anômalo) ou `null` se o modelo não foi treinado. O semáforo segue a regra; o modelo é um indicador à parte, que aponta leituras fora do padrão do sensor mesmo abaixo dos limiares. Validações (`src/schemas.py`): campos obrigatórios, campos extras recusados, tipos estritos (texto como `"1.5"` não vira número), NaN/infinito recusados, `timestamp` ISO 8601 com fuso e não no futuro, e limites operacionais (`rms` 0–100 mm/s, `curtose` 1–1024, `assimetria` ±32, `frequencia_pico` 0–1024 Hz, `rotacao_rpm` > 0 e ≤ 10 000). Erros voltam em português:

```json
{"detail": [{"campo": "rms", "mensagem": "deve ser maior ou igual a 0", "recebido": -1}]}
```

---

## Esquema do Banco de Dados (`mock/schema.sql`)

```mermaid
erDiagram
    ativos ||--o{ sensores : possui
    sensores ||--o{ leituras_brutas : gera
    leituras_brutas ||--o{ alertas : origina
    sensores ||--o{ alertas : "referente a"
```

| Tabela | Colunas principais | Restrições |
|---|---|---|
| `ativos` | `id`, `tag` (ex.: MOT-101), `nome`, `tipo`, `localizacao`, `rpm_nominal` | `tag` única · `tipo` ∈ {MOTOR, COMPRESSOR} · `rpm_nominal` > 0 |
| `sensores` | `id`, `ativo_id`, `posicao` (ex.: LADO_ACOPLADO), `taxa_amostragem_hz` (2048), `unidade` (mm/s) | `ativo_id` → `ativos` |
| `leituras_brutas` | `id`, `sensor_id`, `timestamp` (ISO 8601 UTC), `rms`, `assimetria`, `curtose`, `frequencia_pico`, `rotacao_rpm`, `status_alerta`, `anomalia_real`, `tipo_anomalia` | `rms` ≥ 0 · `frequencia_pico` ≥ 0 · `status_alerta` ∈ {NORMAL, ATENCAO, CRITICO} · índice em (`sensor_id`, `timestamp`) |
| `alertas` | `id`, `leitura_id`, `sensor_id`, `timestamp`, `severidade`, `mensagem`, `reconhecido` | `severidade` ∈ {ATENCAO, CRITICO} · FKs para `leituras_brutas` e `sensores` |

> `anomalia_real` e `tipo_anomalia` são o **gabarito do simulador**: existem só no mock, para avaliar o detector. **Não devem ser usadas como feature** do modelo (vazamento de dados).

A curtose é guardada na forma não-excesso (distribuição normal ≈ 3).

**Critérios de status** (ISO 10816 adaptada, em `services/regras.py`):

| Status | Condição |
|---|---|
| 🟢 NORMAL | dentro dos limites |
| 🟡 ATENCAO | RMS ≥ 4,5 ou curtose ≥ 4 (ou RMS < 0,2: possível sensor travado) |
| 🔴 CRITICO | RMS ≥ 7,1 ou curtose ≥ 8 |

---

## Escopo do MVP

**Limite de esforço:** 42 horas de desenvolvimento.

**Dentro do escopo**

1. Ingestão de dados históricos/sintéticos (SQLite, CSV, JSON e `POST /api/dados`) com validação.
2. Indicadores por janela: RMS, assimetria, curtose, frequência de pico.
3. Classificação por regra de limiar e detecção de anomalias com Isolation Forest.
4. Dashboard web com semáforo (verde, amarelo, vermelho) por ativo/sensor.

**Fora do escopo**

- Conexão direta com CLP/sensores via **OPC-UA** ou **MQTT**.
- Envio de alertas por **SMS, WhatsApp** ou e-mail.
- Análise espectral completa (**FFT**); o MVP usa apenas a frequência de pico já calculada por janela.
- Classificadores supervisionados (não há base balanceada de falhas rotuladas).
- Autenticação e controle de acesso de usuários.

---

## Requisitos

### Funcionais

| ID | Requisito | Status |
|---|---|---|
| RF01 | O sistema deve ingerir leituras de vibração a partir de SQLite, CSV, JSON e `POST /api/dados`, rejeitando registros inválidos com o motivo. | Pronto |
| RF02 | O sistema deve disponibilizar, por janela, os indicadores RMS, assimetria, curtose, frequência de pico e rotação, e permitir consultar as últimas leituras. | Pronto |
| RF03 | O sistema deve classificar cada leitura como NORMAL, ATENCAO ou CRITICO por regra de limiar. | Pronto |
| RF04 | O sistema deve detectar anomalias com Isolation Forest, sem depender de falhas rotuladas. | Pronto |
| RF05 | O sistema deve registrar um alerta na tabela `alertas` quando o status de um sensor piorar. | Pronto |
| RF06 | O dashboard deve exibir o status por cores de cada ativo/sensor e a lista de alertas. | Pronto |
| RF07 | A API deve expor `GET /health` informando a situação da conexão com o banco. | Pronto |
| RF08 | O fluxo deve funcionar ponta a ponta: simulador → API → banco → painel, com o painel indicando carregamento e falha de comunicação. | Pronto (`simulator.py --api`; testado em `src/test_api.py` e `dashboard/test_dashboard.py`) |

### Não funcionais

| ID | Requisito | Status |
|---|---|---|
| RNF01 | A resposta de uma inferência sobre o conjunto de dados do mock (≈ 5 mil leituras) deve levar menos de 3 s. | Atendido (testado em `services/test_modelo.py`) |
| RNF02 | O projeto deve ser executável a partir de um clone limpo seguindo apenas este README; os dados do simulador devem ser reprodutíveis (`--seed`). | Atendido (validado em 01/11/2026: clone limpo, `venv` novo, Python 3.12, 68 testes passando e as mesmas métricas do modelo) |
| RNF03 | O modelo treinado deve ser salvo e carregado com `joblib`, sem retreinar a cada inicialização. | Atendido |
| RNF04 | Configurações e segredos ficam no `.env`; `.env` e `*.db` não são versionados. | Atendido |
| RNF05 | A lógica de leitura/validação e o simulador devem ter testes automatizados. | Atendido (`mock/`, `services/`, `src/`, `dashboard/`) |

---

## Limitações Conhecidas

- Os dados são sintéticos; a validação com dados reais da planta depende da disponibilidade fornecida pela empresa.
- Os limiares da regra são uma adaptação da ISO 10816, não calibrados para os ativos reais.
- O Isolation Forest tem ~0,77 de precisão no teste: cerca de 1 em cada 4 avisos do modelo é falso alarme. Por isso ele não muda o semáforo, só sinaliza.
- O modelo aprende o "normal" de cada sensor com dados sintéticos; com dados reais precisa ser retreinado (`python -m services.modelo`).
- Alertas são gerados pela regra (status piorou), não pelo modelo.

---

## Licença

Projeto desenvolvido para fins acadêmicos e de aplicação prática no contexto da ArcelorMittal / Tuper.
