# AI Log — Diário de Engenharia Assistida por IA

* **Projeto:** Sistema Inteligente de Diagnóstico Preditivo de Falhas Mecânicas (ArcelorMittal / Tuper)
* **Equipe:** Ederlane Ciribelle Silva Fernandes, Iran Andrei da Costa, Paulo Ricardo Wosniak Soares
* **Repositório:** https://github.com/iranCosta/Projeto-Aplicado-II

> Trechos marcados com **[EQUIPE: ...]** ainda precisam ser preenchidos pelos integrantes. Prompts que não foram guardados e forem reconstruídos de memória devem ser marcados como *(reconstruído)*.

---

## 1. Ferramental Utilizado

* **Modelos / Plataformas:**
  * Claude (Anthropic): simulador e dados (Aula 03). [EQUIPE: versão do modelo e quem usou]
  * Claude Opus 5.5 no Claude Code (app desktop): testes da regra (Aula 05) e API com validação (Aula 06), sessão da Ederlane.
  * [EQUIPE: outras ferramentas usadas na Semana 02, Aula 04 e Aula 05, ex.: ChatGPT, Gemini]
* **Assistentes de IDE:** [EQUIPE: ex.: Copilot, Cursor — ou "nenhum"]

---

## 2. Registro Semanal de Interações Técnicas

### Sprint 1 / Semana 02 — Definição do MVP e da arquitetura (24/09/2026)

**1. Contexto e Objetivo da Tarefa**

* Escolher o problema real (manutenção preditiva de motores e compressores na ArcelorMittal / Tuper), recortar um MVP que caiba em 42 horas e definir a stack.

**2. Principais Prompts e Contexto Fornecido**

* **Prompt 1:** `[EQUIPE: cole aqui o prompt usado para definir a arquitetura/MVP]`
* **Contexto adicional:** [EQUIPE: o que foi passado à IA — ex.: descrição do problema da Tuper, limite de 42 h, tipos de máquina]

**3. Avaliação da Resposta Gerada**

* **O que funcionou de primeira (sugestões úteis da IA):**
  * Indicadores estatísticos por janela de vibração: RMS, assimetria e curtose.
  * **Isolation Forest**, por ser não supervisionado: não exige uma base de falhas rotuladas, que a planta não tem.
  * Status por cores (🟢 Normal, 🟡 Atenção, 🔴 Crítico) para o painel.
  * Pipeline em 4 etapas: ingestão → indicadores → detecção → dashboard.
* **Falhas, alucinações ou exageros:**
  * O primeiro escopo (README de 24/09) falava em painel "em tempo real" e "análises estatísticas avançadas", o que não é viável sem conexão com a planta.
  * A camada de visualização ficou indefinida ("Streamlit / Dash / Framework Web").
  * [EQUIPE: outras sugestões que não fizeram sentido]

**4. Intervenção Humana e Refatoração**

* **Descartado por ser complexo demais para 42 h:**
  * Conexão direta com CLP/sensores via OPC-UA ou MQTT (usamos dados sintéticos).
  * Envio de alertas por SMS, WhatsApp ou e-mail.
  * Análise espectral completa (FFT): usamos só a frequência de pico por janela.
  * Classificadores supervisionados: não há base balanceada de falhas rotuladas.
  * Autenticação e controle de acesso.
* **Decisão final da equipe:**
  * MVP com dados simulados.
  * Backend em FastAPI + SQLite.
  * Detecção combinando regra por limiar (ISO 10816 adaptada) e Isolation Forest.
  * Dashboard em Streamlit consumindo a API.
  * [EQUIPE: confirmar e justificar a decisão com as palavras de vocês]

---

### Sprint 1 / Aula 03 — Dados e Mocks Industriais (01/10/2026)

**1. Contexto e Objetivo da Tarefa**

* Modelar um banco enxuto e criar um simulador de vibração com ~90% de operação normal e ~10% de anomalias, para o sistema ter o que detectar.

**2. Principais Prompts e Contexto Fornecido**

* **Prompt 1:** `[EQUIPE: prompt usado para o schema e o simulador]`
* **Contexto adicional:** [EQUIPE: ex.: tabelas sugeridas pelo professor, ativos da Tuper, limite de 3 a 5 tabelas]

**3. Avaliação da Resposta Gerada**

* **O que funcionou de primeira:**
  * Esquema enxuto com 4 tabelas (`ativos`, `sensores`, `leituras_brutas`, `alertas`), com DDL em SQLite e restrições CHECK/FK.
  * `mock/simulator.py` (modos lote e stream), `mock/validar.py` e `mock/test_mock.py`.
  * Anomalias fisicamente plausíveis (desbalanceamento, desalinhamento, rolamento, pico isolado, sensor travado), com degradação progressiva.
  * `mock/leitor_dados.py`: carregador unificado (SQLite/CSV/JSON), validação com separação das linhas rejeitadas, resumo por sensor e baseline com Isolation Forest (um modelo por sensor).
* **Falhas, alucinações ou código quebrado:**
  * A anomalia de rolamento saiu com curtose ~3,3, indistinguível do normal, porque os pulsos longos se sobrepunham.
  * O desalinhamento gerava RMS médio ~2,2, abaixo do limiar de atenção, ou seja, a anomalia não seria detectada.
  * A fração de anomalias varia por semente (7–10% em vez de exatos 10%), porque os episódios são aleatórios.

**4. Intervenção Humana e Refatoração**

* Pulsos do rolamento encurtados e amplitude ajustada → curtose média ~5.
* Amplitude da componente 2x do desalinhamento aumentada.
* O teste de proporção passou a aceitar 5–15% de anomalias.
* [EQUIPE: correções feitas à mão — ex.: conferência dos limiares com a ISO 10816, nomes e tags dos ativos (MOT-101 etc.), unidade mm/s, curtose na forma não-excesso (~3)]
* **Resultado medido no mock (5.000 leituras):**
  * Isolation Forest: recall ~0,85 e precisão ~0,83.
  * Regra de limiar: recall ~0,57 e precisão 1,0.
  * A regra deixa passar o início da degradação, e é aí que o modelo agrega valor.

---

### Sprint 1 / Aula 04 — Estrutura do backend, banco e `/health` (08/10/2026)

**1. Contexto e Objetivo da Tarefa**

* Organizar o repositório, conectar a aplicação ao SQLite e expor uma rota de healthcheck provando que a infraestrutura funciona.

**2. Principais Prompts e Contexto Fornecido**

* **Prompt 1:** `[EQUIPE: prompt usado para gerar o scaffold da API]`
* **Prompt 2:** o prompt de continuidade usado para retomar o projeto em outra sessão de IA foi guardado em [`docs/prompt_continuidade.md`](docs/prompt_continuidade.md).
* **Contexto adicional:** estrutura atual do repositório, `mock/schema.sql`, ambiente Windows + Git Bash + Python 3.13.

**3. Avaliação da Resposta Gerada**

* **O que funcionou de primeira:**
  * Camadas separadas (`routes` → `controllers` → `models` → `database`).
  * `src/config.py` lendo o `.env`.
  * `init_db()` criando as tabelas a partir do `schema.sql`.
  * `GET /health` com 200/503.
  * Consultas SQL parametrizadas.
* **Falhas, alucinações ou código quebrado:**
  * O schema inicial de `POST /api/dados` aceitava `status_alerta` enviado pelo cliente e `timestamp` como texto livre. Isso foi corrigido na Aula 06. [EQUIPE: confirmar que esse trecho foi gerado pela IA]
  * [EQUIPE: outros erros da IA nesta etapa]

**4. Intervenção Humana e Refatoração**

* Problemas de organização encontrados na auditoria do repositório (não necessariamente causados pela IA):
  * Estrutura duplicada `mock/mock/` depois do upload.
  * `.gitignore` enviado como `.gitignore.txt`, um nome que o Git não reconhece.
  * `.pyc` e `mock/data/vibracao.db` versionados.
* Achatamento de `mock/mock` → `mock` (commit `6d37d09`).
* Renomeação de `.gitignore.txt` para `.gitignore`.
* Remoção dos `.pyc` do controle de versão.
* `vibracao.db` e os `.pyc` de `services/` deixaram de ser versionados na Aula 05 (commit `4d36672`).
* [EQUIPE: outros ajustes manuais]

---

### Sprint 2 / Aula 05 — Núcleo da regra de negócio (21/10/2026; testes em 01/11/2026)

**1. Contexto e Objetivo da Tarefa**

* Implementar a regra de diagnóstico como função pura em `services/regras.py`: recebe os indicadores de uma janela e devolve NORMAL / ATENCAO / CRITICO com os motivos, tratando entradas inválidas.

**2. Principais Prompts e Contexto Fornecido**

* **Prompt 1:** `[EQUIPE: prompt que gerou a lógica inicial de services/regras.py]`
* **Prompt 2 (01/11, Claude Code):** as orientações da Aula 05 foram coladas no chat com o pedido de avaliar se o projeto as atendia; depois veio a autorização para implementar o que faltava.
* **Contexto adicional:** limiares do `simulator.py` (ISO 10816 adaptada) e o código existente.

**3. Avaliação da Resposta Gerada**

* **O que funcionou de primeira:**
  * Função pura com limiares em constantes (RMS 4,5 / 7,1 mm/s; curtose 4 / 8; RMS < 0,2 = sensor travado).
  * O nível crítico é avaliado antes do de atenção.
  * Exceção própria `DadosInvalidosError` para leitura vazia, campos ausentes, sensor inexistente, NaN, infinito, texto, booleano, valores negativos e rotação ≤ 0.
  * Conferido em 01/11: a regra e o classificador do simulador dão o mesmo status nas 3.000 leituras.
* **Falhas, alucinações ou código quebrado:**
  * O tipo do `sensor_id` não era validado: `"1"`, `None`, `0`, `-3` e `1.0` passavam.
  * Não havia script de teste nem demonstração no terminal, que a aula exigia.
  * Bug encontrado ao rodar os testes no Windows: em `mock/leitor_dados.py`, `with sqlite3.connect(...)` não fecha a conexão (só faz commit). O arquivo `.db` ficava travado e a limpeza dos testes falhava.

**4. Intervenção Humana e Refatoração**

* Validação de `sensor_id` como inteiro positivo.
* `python -m services.regras`: demonstração com os 3 cenários (perfeito, crítico, erro de entrada).
* `services/test_regras.py`: 14 testes (cada status, limites exatos, prioridade do crítico, função pura, entradas inválidas).
* Correção da conexão em `leitor_dados.py` com `contextlib.closing`.
* [EQUIPE: ajustes matemáticos ou de regra feitos por vocês na versão original — ex.: escolha dos limiares, ordem crítico → atenção]

---

### Sprint 2 / Aula 06 — Exposição de endpoints e validação de payloads (01/11/2026)

**1. Contexto e Objetivo da Tarefa**

* Ligar a regra de negócio a rotas HTTP:
  * `POST` que valida o payload e aplica a regra.
  * `GET` com os resultados processados.
  * Respostas 201 / 422 com mensagens claras.

**2. Principais Prompts e Contexto Fornecido**

* **Prompt 1 (Claude Code):** as orientações da Aula 06 foram coladas no chat com o pedido de avaliar se o projeto já as atendia. A IA listou o que faltava e depois recebeu a instrução "seguir" para implementar.
* **Contexto adicional:** acesso ao repositório completo, ao banco gerado pelo simulador (para conferir as faixas reais de cada indicador) e ao `services/regras.py`.

**3. Avaliação da Resposta Gerada**

* **O que funcionou de primeira:**
  * Esquema `LeituraIn` (Pydantic v2) com tipos estritos e limites operacionais justificados:
    * `frequencia_pico` ≤ 1024 Hz (limite de Nyquist, para amostragem de 2048 Hz).
    * Curtose de 1 a 1024 e |assimetria| ≤ 32: limites matemáticos para 1024 amostras.
  * `POST /api/dados` chamando `diagnosticar_leitura()` e gravando o status calculado.
  * `GET /api/diagnosticos` (filtros por sensor e status) e `GET /api/status` (último status de cada sensor).
  * Erros em português num formato único; 503 quando o banco está indisponível.
  * 18 testes com `TestClient` num banco temporário, aprovados na primeira execução.
* **Validações cruciais que a IA havia esquecido no schema original (Aula 04):**
  * `status_alerta` vinha do cliente: quem chamava a API decidia se a leitura era crítica.
  * `timestamp` como `str`: aceitava `"abc"`.
  * Sem `gt=0` em `sensor_id` e `rotacao_rpm`, sem limites superiores e com campos extras aceitos em silêncio.
  * `float` do Pydantic aceita NaN e infinito por padrão, e o JSON do Python também aceita `NaN`.
  * Sem mensagens de erro personalizadas.
* **Pontos de atenção da nova versão:**
  * Os limites superiores (RMS ≤ 100 mm/s, rotação ≤ 10.000 rpm) foram escolhidos pela IA com folga. Não estão calibrados para os ativos da Tuper.
  * O `TestClient` emite um aviso de descontinuação do `httpx` com o Starlette.

**4. Intervenção Humana e Refatoração**

* Revisão do diff e autorização de cada commit pela equipe (commit `7a94f01`).
* [EQUIPE: teste manual pelo Swagger `/docs` — registrar os casos testados e o resultado]
* [EQUIPE: revisar os limites operacionais com quem conhece os equipamentos]
* Mudança incompatível: `POST /api/dados` não aceita mais `status_alerta`, então os clientes antigos precisam ser ajustados. [EQUIPE: confirmar que o Iran e o Paulo foram avisados]

---

## 3. Síntese Crítica de Encerramento (Preenchida na Semana 13)

* **Onde a IA mais acelerou a entrega:** [preencher na Semana 13]
* **Onde a IA mais atrapalhou ou gerou retrabalho:** [preencher na Semana 13]
* **Lições aprendidas de engenharia de software:** [preencher na Semana 13]
