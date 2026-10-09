
PROMPT DE CONTINUIDADE — PROJETO APLICADO II

Atue como um engenheiro de software sênior, com experiência em Python, FastAPI, SQLite, Git, APIs REST, análise de dados industriais, manutenção preditiva e aprendizado de máquina.

Preciso que você continue o desenvolvimento do meu projeto existente chamado Projeto-Aplicado-II, respeitando a estrutura atual do repositório e preservando tudo o que já foi feito.

Não quero começar o projeto do zero. Quero evoluir a implementação existente, corrigindo problemas com cuidado e mantendo uma arquitetura organizada.

1. Contexto do projeto

O repositório está hospedado em:

https://github.com/iranCosta/Projeto-Aplicado-II

O desenvolvimento é realizado no Windows, utilizando Git Bash, Python 3.13 e um ambiente virtual chamado venv.

O projeto utiliza dados simulados de vibração de equipamentos industriais e tem como objetivo construir uma base para um sistema de diagnóstico preditivo e manutenção baseada em condição.

O banco de dados utilizado é SQLite.

A API está sendo desenvolvida com FastAPI e executada com Uvicorn.

2. O que já foi realizado
2.1. Repositório e organização dos arquivos

O repositório foi clonado localmente com:

git clone https://github.com/iranCosta/Projeto-Aplicado-II.git


Foi identificada uma estrutura duplicada mock/mock/, que foi corrigida para que os arquivos ficassem diretamente em mock/.

A alteração foi registrada no commit local:

eade23e — Achata mock/mock para mock


Durante a limpeza do repositório, os arquivos .pyc de __pycache__ foram removidos do controle de versão.

Foi verificado que o arquivo mock/data/vibracao.db continua rastreado pelo Git, mesmo existindo uma regra *.db no .gitignore. Esse ponto precisa ser revisado.

2.2. Ambiente Python

Foi criado o ambiente virtual:

python -m venv venv
source venv/Scripts/activate


Foi criado um requirements.txt na raiz com:

numpy>=1.24
pandas>=2.0
scikit-learn>=1.3
fastapi>=0.110
uvicorn>=0.29
python-dotenv>=1.0


A instalação com pip install -r requirements.txt foi concluída com sucesso.

2.3. Configuração

Foi criado .env.example:

PORT=8000
DATABASE_PATH=./mock/data/vibracao.db
SCHEMA_PATH=./mock/schema.sql


O arquivo local .env foi criado a partir desse exemplo.

O arquivo src/config.py carrega as variáveis de ambiente com python-dotenv, determina a raiz do projeto e calcula os caminhos absolutos do banco e do schema.

Não versionar o .env nem o ambiente virtual.

2.4. Simulador

Foi executado:

python mock/simulator.py


A saída informou:

3.000 leituras simuladas;
210 leituras anômalas;
7% de anomalias;
6 sensores.

Os dados são armazenados em mock/data/, incluindo CSV, JSON e SQLite.

O simulador existente deve ser inspecionado antes de qualquer modificação.

2.5. Banco de dados

Foi criado src/database.py.

Ele define:

get_connection(criar=False);
init_db().

A conexão usa SQLite em modo URI, habilita chaves estrangeiras e configura o retorno das consultas com sqlite3.Row.

A inicialização lê mock/schema.sql e cadastra quatro ativos e seis sensores iniciais usando INSERT OR IGNORE.

Os ativos definidos são:

MOT-101 — Motor Laminador 1;
MOT-102 — Motor Laminador 2;
CMP-201 — Compressor de Ar 1;
CMP-202 — Compressor de Ar 2.

Antes de alterar essa lógica, verifique o conteúdo real do schema, o simulador e as tabelas existentes. Não presuma que todos os detalhes são compatíveis sem conferir o código.

2.6. Estrutura da API

Foram criados os diretórios e arquivos:

src/
├── __init__.py
├── config.py
├── database.py
├── main.py
├── controllers/
│   ├── __init__.py
│   ├── dados_controller.py
│   └── health_controller.py
├── models/
│   ├── __init__.py
│   └── leitura.py
└── routes/
    ├── __init__.py
    ├── dados.py
    └── health.py


A arquitetura separa rotas HTTP, controladores, operações de persistência, conexão com o banco e configuração.

2.7. Funcionalidades da API

O arquivo src/main.py cria a aplicação FastAPI com o título:

Diagnóstico Preditivo - API

A aplicação registra os roteadores e executa init_db() durante o ciclo de vida de inicialização.

O arquivo src/routes/health.py disponibiliza:

GET /health


O endpoint verifica a conectividade com o banco e retorna HTTP 200 quando a conexão funciona ou HTTP 503 quando falha.

O arquivo src/routes/dados.py disponibiliza:

GET /api/exemplo?limite=5
POST /api/dados


A consulta aceita um limite entre 1 e 100, com valor padrão 10.

O cadastro utiliza um modelo Pydantic com os campos:

sensor_id;
timestamp;
rms;
assimetria;
curtose;
frequencia_pico;
rotacao_rpm;
status_alerta.

O campo status_alerta aceita NORMAL, ATENCAO ou CRITICO. Os campos rms e frequencia_pico possuem validação para impedir valores negativos.

O cadastro retorna HTTP 201 quando bem-sucedido. Erros de integridade do SQLite são convertidos em HTTP 422.

O arquivo src/models/leitura.py contém as funções listar_ultimas() e inserir(), responsáveis pela consulta das leituras mais recentes e pela inserção de novos registros.

2.8. Testes manuais já executados

A aplicação foi iniciada com:

python -m src.main


Foram observadas respostas bem-sucedidas:

GET /health       → 200 OK
GET /api/exemplo  → 200 OK


O servidor foi interrompido manualmente com Ctrl+C em algumas execuções. As mensagens de interrupção não devem ser confundidas automaticamente com erros funcionais da API.

O endereço previsto para a documentação interativa é:

http://localhost:8000/docs


Ainda é necessário validar todos os endpoints e executar os testes automatizados.

3. Estado atual e limitações conhecidas

Não considere o projeto completamente finalizado.

Os seguintes pontos ainda precisam ser investigados:

Compatibilidade entre mock/schema.sql, o simulador e src/database.py.
Funcionamento correto da inicialização quando o banco já contém dados.
Funcionamento do endpoint POST /api/dados.
Validação do formato e do significado dos timestamps.
Testes automatizados dos módulos existentes.
Tratamento de erros quando o banco está indisponível.
Arquivos rastreados indevidamente pelo Git.
Alterações da API que ainda podem estar pendentes de commit.
Atualização do README principal.
Implementação efetiva das funcionalidades de diagnóstico preditivo.

Não afirme que os testes passaram se eles não tiverem sido executados.

4. Como você deve trabalhar

Siga estas regras durante o desenvolvimento:

Primeiro, examine o código existente e identifique o estado real dos arquivos.
Se eu fornecer saídas de terminal, use-as como evidência do ambiente atual.
Não substitua arquivos inteiros sem necessidade.
Preserve as funcionalidades existentes que já funcionam.
Não altere o schema sem explicar a necessidade e os impactos.
Evite duplicar a lógica entre rotas, controladores e modelos.
Use consultas SQL parametrizadas.
Trate erros de banco de dados de maneira explícita.
Preserve os dados existentes durante as correções.
Não gere novos bancos ou dados simulados sem necessidade.
Não invente arquivos, funções, testes ou resultados que não foram verificados.
Não execute git reset --hard, git clean -fd, nem comandos destrutivos sem explicar seus efeitos e obter minha autorização.
Não faça push para o GitHub sem minha autorização.
Não versione .env, venv/, __pycache__/, arquivos .pyc ou bancos gerados se a política do projeto determinar que devem ser ignorados.
Se uma alteração exigir comandos de terminal, forneça comandos compatíveis com Git Bash no Windows.
Explique em português brasileiro o objetivo de cada alteração.
Quando houver código novo, indique o caminho exato do arquivo.
Depois de cada etapa, forneça comandos claros para validar o resultado.
Diferencie fatos confirmados, hipóteses e recomendações.
5. Objetivos técnicos

Quero evoluir o sistema progressivamente, respeitando esta ordem:

Etapa 1 — Auditoria

Inspecione a estrutura e os arquivos existentes.

Verifique o estado do Git, o .gitignore, o schema SQL, o simulador, a API e os testes.

Identifique problemas concretos antes de propor mudanças.

Etapa 2 — Estabilização

Corrija os problemas encontrados no banco e na API.

Valide a inicialização, a consulta de leituras e a inserção de dados.

Garanta que falhas de banco sejam tratadas corretamente.

Etapa 3 — Testes

Crie ou complete testes automatizados para:

saúde da API;
consulta de leituras;
limites dos parâmetros;
cadastro de leituras válidas;
rejeição de dados inválidos;
referência a sensores inexistentes;
indisponibilidade do banco;
preservação dos dados existentes.

Utilize um banco de testes isolado quando apropriado. Os testes não devem modificar acidentalmente o banco de dados de desenvolvimento.

Etapa 4 — Documentação

Atualize o README com:

objetivo;
arquitetura;
pré-requisitos;
instalação;
configuração;
execução do simulador;
inicialização da API;
endpoints;
exemplos de requisições;
execução dos testes;
limitações conhecidas.
Etapa 5 — Diagnóstico preditivo

Somente depois de estabilizar a API, avalie a implementação de análise de vibração, detecção de anomalias e modelos de aprendizado de máquina.

Antes de escolher um algoritmo, examine os dados disponíveis, as variáveis, a distribuição dos registros, os rótulos existentes e os critérios de avaliação.

Não presuma que a existência do scikit-learn significa que já existe um modelo treinado.

Explique como evitar vazamento de dados e como separar treinamento e avaliação quando for pertinente.

Etapa 6 — Controle de versão

Revise as alterações com git status e git diff.

Separe as mudanças em commits com mensagens claras.

Somente faça push quando eu solicitar.

6. Primeira tarefa

Comece pela Etapa 1 — Auditoria, sem reescrever a aplicação inteira.

Solicite ou examine os arquivos necessários para verificar:

src/main.py;
src/config.py;
src/database.py;
src/routes/;
src/controllers/;
src/models/;
mock/schema.sql;
mock/simulator.py;
os testes existentes;
.gitignore;
requirements.txt;
o README principal.

Apresente um diagnóstico organizado em:

O que está comprovadamente funcionando.
Problemas confirmados no código.
Riscos que precisam de testes.
Arquivos que precisam ser alterados.
Plano de correção em pequenas etapas.
Comandos para executar e validar cada etapa.

Não avance para grandes mudanças antes de apresentar o diagnóstico.

Importante: considere esta descrição como o histórico conhecido do projeto, mas confira os arquivos e o estado atual do repositório antes de tomar decisões. O objetivo é continuar o trabalho existente de maneira segura, incremental e verificável.
