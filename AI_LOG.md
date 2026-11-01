# AI Log — Diário de Engenharia Assistida por IA

* **Projeto:** Sistema Inteligente de Diagnóstico Preditivo de Falhas Mecânicas (ArcelorMittal / Tuper)
* **Equipe:** Ederlane Ciribelle Silva Fernandes, Iran Andrei da Costa, Paulo Ricardo Wosniak Soares
* **Repositório:** https://github.com/iranCosta/Projeto-Aplicado-II

> Trechos marcados com **[EQUIPE: ...]** ainda precisam ser preenchidos pelos integrantes. Prompts que não foram guardados e forem reconstruídos de memória devem ser marcados como *(reconstruído)*.

---

## 1. Ferramental Utilizado

* **Modelos / Plataformas:**
  * Claude (Anthropic): simulador e dados (Aula 03). [EQUIPE: versão do modelo e quem usou]
  * Claude Opus 5.5 no Claude Code (app desktop): testes da regra (Aula 05), API com validação (Aula 06) e painel Streamlit (Aula 07), sessão da Ederlane.
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

### Sprint 2 / Aula 07 — Construção da Interface do Utilizador (01/11/2026)

**1. Contexto e Objetivo da Tarefa**

* Criar a tela operacional do Projeto 1 (painel de monitoramento), legível a 2 metros, com:
  * gráfico temporal de RMS;
  * semáforo (verde / amarelo / vermelho);
  * caixa de texto com o diagnóstico.

**2. Principais Prompts e Contexto Fornecido**

* **Prompt 1 (Claude Code):** as orientações da Aula 07 e as instruções extras do Projeto 1 foram coladas no chat com o pedido de "continuar".
* **Contexto adicional:**
  * Decisão do README de usar Streamlit lendo os dados só pela API.
  * Endpoints `/api/status` e `/api/diagnosticos` da Aula 06.
  * Banco gerado pelo simulador.

**3. Avaliação da Resposta Gerada**

* **O que funcionou de primeira:**
  * `dashboard/cliente.py` (chamadas HTTP com timeout e erro próprio quando a API cai).
  * Cartões grandes por sensor, com contraste alto e pulso no estado crítico.
  * Resumo "X críticos · Y em atenção · Z normais".
  * Seleção automática do primeiro sensor com problema.
  * Gráfico Altair de RMS e curtose com linhas tracejadas nos limiares da regra (importados de `services/regras.py`, sem duplicar valores).
  * Atualização automática a cada 10 s.
  * 4 testes com `streamlit.testing.v1.AppTest`, com a API simulada.
* **Falhas e problemas encontrados ao ver o painel rodando:**
  * A caixa de diagnóstico usava `st.error` / `st.success`: texto pequeno e pouco contraste no tema escuro, ilegível a 2 m.
  * O eixo do gráfico mostrava os dias em inglês ("Fri 09") e a legenda mostrava "ATENCAO" sem acento.
  * `use_container_width` está obsoleto na versão 1.66 do Streamlit.
  * O endpoint `/api/diagnosticos` limitava a 100 leituras, pouco para um gráfico temporal.
  * Leituras novas, com horário atual, ao lado do lote histórico do simulador (09/10) deixam um salto de semanas no gráfico.

**4. Intervenção Humana e Refatoração**

* Caixa de diagnóstico refeita em HTML no mesmo padrão dos cartões (fonte grande, cor do estado).
* Eixo no formato `dd/mm HH:MM` e legenda com acentos.
* Troca para `width="stretch"`.
* Limite de `/api/diagnosticos` ampliado para 500.
* README orienta usar `--recriar` no modo stream para evitar o salto no gráfico.
* As duas leituras de teste enviadas para conferir as cores foram apagadas do banco local.
* [EQUIPE: ajustes de estilo ou usabilidade feitos por vocês depois de ver o painel — ex.: tamanho de fonte num monitor real, ordem dos cartões]
* O "diagnóstico emitido pelo modelo preditivo" pedido para o Projeto 1 foi adicionado na etapa seguinte (Isolation Forest).

---

### Sprint 2 / Isolation Forest e persistência com joblib (01/11/2026, antes das orientações da Aula 08)

**1. Contexto e Objetivo da Tarefa**

* Treinar o detector de anomalias (RF04) e salvá-lo com joblib (RNF03).
* Avaliá-lo de forma honesta contra a regra de limiar.
* Mostrar o resultado na API e no painel, que é o "diagnóstico emitido pelo modelo preditivo" do Projeto 1.

**2. Principais Prompts e Contexto Fornecido**

* **Prompt 1 (Claude Code):** "próximo passo", depois de a IA sugerir o Isolation Forest como próxima etapa.
* **Contexto adicional:**
  * Experimento existente em `mock/leitor_dados.py --detectar`.
  * Prompt de continuidade, que pede separar treino e avaliação e evitar vazamento de dados.
  * Banco do simulador com gabarito.

**3. Avaliação da Resposta Gerada**

* **O que funcionou de primeira:**
  * `services/modelo.py`: um Isolation Forest por sensor, divisão temporal 70/30, comparação com a regra, salvamento com joblib (comprimido de 8,5 MB para 2,1 MB).
  * `src/ia.py`: carrega o modelo uma vez na inicialização; sem o arquivo, a API segue só com a regra.
  * Campo `modelo` (anomalia e score) em todas as respostas de leitura e situação do modelo no `/health`.
  * Painel: aviso no cartão, linha do modelo na caixa de diagnóstico e anel no gráfico nas leituras anômalas.
* **Falhas, alucinações ou código quebrado:**
  * O experimento original treinava e avaliava nos mesmos dados (recall 0,93 otimista). Com teste separado, o resultado ficou em recall 0,94 e precisão 0,77 (Isolation Forest), contra recall 0,62 e precisão 1,0 (regra).
  * `pontuar()` quebrava com índice repetido no DataFrame. O teste de desempenho (RNF01) encontrou o erro e a função passou a trabalhar por posição.
  * Os testes da API passavam a carregar o modelo real da pasta e dependiam do ambiente. Foram isolados com `MODELO_PATH` temporário e um modelo sintético.
  * No painel, o aviso do modelo deixava um cartão mais alto e desalinhava a grade, e o detalhe não abria no sensor marcado pelo modelo.

**4. Intervenção Humana e Refatoração**

* Decisão de projeto: o semáforo continua sendo o da regra (determinística, sem falsos alarmes), e o modelo aparece como indicador à parte. Motivo: precisão de 0,77, ou seja, cerca de 1 em cada 4 avisos do modelo é falso. [EQUIPE: confirmar ou rever essa decisão]
* Espaço do aviso reservado em todos os cartões. A prioridade do detalhe passou a ser crítico → atenção → anômalo pelo modelo.
* Leitura de teste (RMS 3,6 com pico em 2× a rotação: regra NORMAL, modelo anômalo) usada para conferir o painel e depois apagada.
* [EQUIPE: comparar com as orientações da Aula 08 quando forem publicadas]

---

### Sprint 2 / Alertas (RF05 e RF06) (01/11/2026, antes das orientações da Aula 08)

**1. Contexto e Objetivo da Tarefa**

* Gravar um alerta quando o status de um sensor piora (RF05), listar e reconhecer alertas pela API e mostrar a lista no painel (RF06).

**2. Principais Prompts e Contexto Fornecido**

* **Prompt 1 (Claude Code):** "continuar", depois de a IA indicar o RF05 como o próximo item do roteiro.
* **Contexto adicional:** a lógica de alerta que já existia no simulador (`gera_alerta`) e a tabela `alertas` do schema, que só o simulador preenchia.

**3. Avaliação da Resposta Gerada**

* **O que funcionou de primeira:**
  * `deve_alertar()` em `services/regras.py`, com o mesmo critério do simulador (piorou em relação à leitura anterior).
  * Leitura e alerta gravados na mesma transação.
  * Comparação com a leitura anterior no tempo, e não com a última inserida, para aceitar leituras atrasadas.
  * `GET /api/alertas` (filtros e total pendente) e `POST /api/alertas/{id}/reconhecer` (idempotente, 404 se não existir).
  * Painel: lista com selo colorido, sensor, horário, mensagem e botão "Reconhecer".
  * Testes da regra, da API e do painel.
* **Falhas, alucinações ou código quebrado:**
  * Os testes do painel passariam a chamar a API real que estava rodando na máquina. Foram isolados com as chamadas de alerta simuladas em todos os testes.
  * A primeira captura de tela depois do clique em "Reconhecer" parecia não ter mudado nada, mas era só a tela ainda atualizando. A API confirmou que o alerta foi reconhecido.

**4. Intervenção Humana e Refatoração**

* `leitura.inserir()` deixou de fazer commit sozinho, para a leitura e o alerta entrarem juntos.
* Teste manual: uma leitura crítica gerou o alerta pela API, e o "Reconhecer" foi clicado no painel. O banco local foi restaurado depois (3.000 leituras e 28 alertas pendentes).
* Limitação mantida: as mensagens dos alertas do simulador têm outro formato que as da API.
* [EQUIPE: decidir se o modelo (Isolation Forest) também deve gerar alertas; hoje só a regra gera]

---

### Sprint 2 / Limpeza técnica (01/11/2026)

**1. Contexto e Objetivo da Tarefa**

* Resolver duas pendências das limitações do README:
  * mensagens de alerta do simulador num formato diferente das da API;
  * endpoint provisório `/api/exemplo`.

**2. Principais Prompts e Contexto Fornecido**

* **Prompt 1 (Claude Code):** escolha da opção "Limpar pendências técnicas" entre as sugestões da IA.

**3. Avaliação da Resposta Gerada**

* **O que funcionou de primeira:**
  * Em vez de só copiar o formato da mensagem, a IA apontou que o simulador tinha uma **cópia própria dos limiares e da classificação**, duplicando `services/regras.py`.
  * O simulador passou a usar `diagnosticar_leitura()` e `deve_alertar()`. Agora existe uma única regra no projeto.
  * Prova de que os dados não mudaram: com a semente 42, os hashes das 3.000 leituras e dos 28 alertas saíram idênticos antes e depois. Só o texto das mensagens mudou.
  * Novo teste no simulador: o status de toda leitura bate com a regra da API, e as mensagens seguem o formato dela.
  * `/api/exemplo` removido, junto com a função de controller e a consulta que só ele usava.
* **Falhas, alucinações ou código quebrado:**
  * Nenhuma nesta etapa.

**4. Intervenção Humana e Refatoração**

* [EQUIPE: quem já tem um `vibracao.db` local continua com as mensagens antigas nos alertas do simulador; basta rodar `python simulator.py` de novo]

---

### Sprint 2 / Aula 08 — Integração Ponta a Ponta e Checkpoint 2 (01/11/2026)

**1. Contexto e Objetivo da Tarefa**

* Fazer o sistema funcionar inteiro: simulador → backend → tela.
* CORS no backend.
* Indicação de carregamento e de erro de comunicação no painel.
* Teste com o simulador rodando em segundo plano.

**2. Principais Prompts e Contexto Fornecido**

* **Prompt 1 (Claude Code):** as orientações da Aula 08 foram coladas no chat. A IA primeiro avaliou o que já era atendido e depois implementou o que faltava.
* **Contexto adicional:** o painel da Aula 07 (que já lia tudo pela API) e o modo `stream` do simulador.

**3. Avaliação da Resposta Gerada**

* **O que já atendia:** o painel não tinha dados fixos no código e já fazia GET e POST na API.
* **Lacuna encontrada:** o modo contínuo do simulador gravava **direto no SQLite**, sem passar pelo backend. A tela mudava, mas não pelo caminho que a aula pede.
* **O que foi feito:**
  * `simulator.py --api URL`: cada leitura vai pelo `POST /api/dados` (só os campos aceitos, sem o gabarito); o terminal mostra o status devolvido pela API, os alertas e os avisos do modelo; se a API cair, o simulador avisa e tenta de novo.
  * CORS com lista de origens locais (`CORS_ORIGINS` no `.env`), métodos `GET` e `POST`.
  * Painel: carregamento na primeira leitura, "Conectado à API · atualizado às …", e, se a API cair, os últimos dados continuam na tela (esmaecidos) com aviso de desde quando está sem comunicação.
  * Testes: CORS (origem local liberada, desconhecida bloqueada), simulador → API com a rede trocada pelo `TestClient` (inclusive com quedas e nova tentativa) e painel com a API caindo depois de responder.
* **Erros e alucinações na integração do front com o back** (só apareceram rodando de verdade, não nos testes):
  * **`localhost` lento no Windows:** cada chamada levava cerca de 2 s, porque o Windows tenta IPv6 (`::1`) antes do IPv4. O simulador fazia uma rodada a cada ~14 s em vez de 1 s, e o painel gastava ~6 s por atualização. Medido: `localhost` 2,07 s contra `127.0.0.1` 0,00 s.
  * **Fuso do gráfico:** o eixo dizia "Horário (UTC)", mas o navegador convertia para o horário de Brasília (01:35, enquanto os cartões mostravam 04:35 UTC). A legenda "atualizado às" também estava no horário local.
  * **Semente diferente da do treino:** com `--seed 11`, o modelo marcava sensores sãos como anômalos (score ~0,5), porque a semente define o "normal" de cada máquina e o modelo foi treinado com a semente 42.
  * O CORS não era necessário para o Streamlit, que chama a API pelo servidor Python; foi configurado porque a aula pede e para qualquer front que rode no navegador.

**4. Intervenção Humana e Refatoração**

* `API_URL` padrão trocado para `http://127.0.0.1:8000` (no `.env.example` e no `cliente.py`).
* Gráfico desenhado em UTC e legenda "atualizado às" em UTC.
* README explica que o simulador deve usar a mesma semente do treino.
* Demonstração ao vivo, num banco vazio de demonstração, com o simulador enviando pela API:
  * Desalinhamento no CMP-201 com RMS 4,03 mm/s: regra NORMAL, modelo anômalo (0,73).
  * Duas leituras depois: regra ATENÇÃO e alerta nº 1.
  * O painel listou os alertas chegando.
  * Com a API derrubada: aviso "Sem comunicação desde …", cartões esmaecidos e simulador tentando de novo.
  * Com a API religada: tudo voltou sozinho.
* [EQUIPE: repetir a demonstração na apresentação do Checkpoint 2]

---

### Fechamento do Sprint 2 (Aulas 05 a 08)

**Principais prompts do Sprint 2**

| Aula | Prompt / pedido | Ferramenta |
|---|---|---|
| 05 | [EQUIPE: prompt que gerou a lógica original de `services/regras.py`]; depois, as orientações da Aula 05 coladas com o pedido de avaliar e completar | [EQUIPE] / Claude Code |
| 06 | Orientações da Aula 06 coladas, "avaliar se atende" e depois "seguir" | Claude Code |
| 07 | Orientações da Aula 07 e instruções extras do Projeto 1, com "continuar" | Claude Code |
| — | "próximo passo" (Isolation Forest), "continuar" (alertas), "limpar pendências técnicas" | Claude Code |
| 08 | Orientações da Aula 08 coladas | Claude Code |

**Onde a IA errou ou deixou passar no Sprint 2**

* **Validação (Aula 06):** o schema original aceitava o status vindo do cliente, texto livre no `timestamp`, NaN e infinito.
* **Avaliação do modelo:** o experimento original media o desempenho nos mesmos dados do treino. O resultado era otimista.
* **Bug de índice repetido em `pontuar()`:** encontrado por um teste.
* **Usabilidade do painel**, vista só com ele rodando:
  * caixa de diagnóstico ilegível no tema escuro;
  * datas em inglês;
  * cartões desalinhados.
* **Integração (Aula 08):**
  * lentidão do `localhost` no Windows;
  * fuso do gráfico errado;
  * simulador ignorando o backend.

**Lição do Sprint 2**

* Os testes automáticos pegaram erros de lógica, mas **três dos problemas de integração só apareceram rodando o sistema de verdade** e olhando a tela e o terminal: a latência, o fuso e o efeito da semente.
* A demonstração ao vivo não substitui os testes, e os testes não substituem a demonstração.

---

## 3. Síntese Crítica de Encerramento (Preenchida na Semana 13)

* **Onde a IA mais acelerou a entrega:** [preencher na Semana 13]
* **Onde a IA mais atrapalhou ou gerou retrabalho:** [preencher na Semana 13]
* **Lições aprendidas de engenharia de software:** [preencher na Semana 13]
