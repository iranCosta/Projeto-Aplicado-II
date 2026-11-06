# Relatório de Auditoria de Setup e Onboarding

* **Projeto Auditado:** Sistema Inteligente de Diagnóstico Preditivo de Falhas Mecânicas
* **Equipe Autora:** Ederlane Ciribelle Silva Fernandes, Iran Andrei da Costa e Paulo Ricardo Wosniak Soares
* **Equipe Auditora:** Gabriel Angelo Foppa, Christoffer Henrique da Silva Souza e Ferdinando Rainert
* **Tempo Gasto para Subir o Sistema:** Não cronometrado. A equipe auditora realizou a avaliação neste workspace, não em clone limpo.
* **Nota de Reprodutibilidade:** 8/10

---

## 1. Diagnóstico do Onboarding Inicial

* **Clone e Dependências:** O `requirements.txt` da raiz inclui as dependências usadas pela API, simulador, testes e dashboard. Instaladas em um ambiente virtual temporário com Python 3.13. O `frontend/package-lock.json` permite instalação reproduzível com `npm ci`. O README, porém, não lista Node.js/npm como pré-requisito, apesar de orientar a execução do frontend.
* **Configuração de Ambiente:** O `.env.example` da raiz contém as variáveis lidas pelo backend, com padrões funcionais. O `frontend/.env.example` contém `VITE_API_URL`, também com endereço local funcional. Ambos correspondem às variáveis observadas no código. A cópia do arquivo do frontend só é documentada com `cp`, sem o equivalente PowerShell.
* **Execução da API e Mock:** Os testes da API passaram via `TestClient`; o lote do simulador também foi executado pela linha de comando e gerou 3.000 leituras em diretório temporário. A API não foi iniciada como processo HTTP durante esta auditoria.
* **Acesso à Interface:** `npm ci` e `npm run build` concluíram com sucesso. A interface não foi aberta no navegador; portanto, CORS e comunicação visual em execução não foram verificados manualmente. Os testes cobrem CORS local e integração simulada do mock com a API.

## 2. Principais Gargalos e Erros Encontrados

* **Erro 1:** O pré-requisito inicial lista Python, mas não lista Node.js e npm. Em uma máquina sem Node/npm, os comandos `npm install` ou `npm ci` não estarão disponíveis.
* **Erro 2:** Na seção do frontend, a cópia do `.env.example` usa `cp`, mas não apresenta o comando equivalente para PowerShell. Use `Copy-Item .env.example .env`.
* **Observação:** A primeira tentativa de testes usou o Python global sem as dependências instaladas e falhou por falta de `numpy` e `requests`. Após instalar `requirements.txt` em um venv temporário, as suítes documentadas passaram; isso confirma a instalação indicada, não uma dependência ausente do projeto.
* **Escopo não coberto:** Não foi feito clone limpo nem medido o tempo de onboarding. Também não houve validação manual da tela no navegador nem inicialização do servidor Uvicorn como processo independente.

## 3. Passo a Passo Corrigido (Guia Definitivo)

Os comandos abaixo são para Windows PowerShell, executados na raiz clonada do repositório. Requerem Python 3.10+ e Node.js/npm compatíveis com Vite 6 (Node.js 18+).

```powershell
# 1. Clonar e entrar no projeto
git clone https://github.com/iranCosta/Projeto-Aplicado-II.git
Set-Location Projeto-Aplicado-II

# 2. Criar o ambiente virtual Python
python -m venv .venv

# 3. Instalar as dependências Python
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 4. Criar a configuração local (opcional; há valores padrão no código)
Copy-Item .env.example .env

# 5. Gerar dados de demonstração em mock/data/vibracao.db
.\.venv\Scripts\python.exe mock\simulator.py --seed 42

# 6. Treinar o modelo salvo em modelos_treinados/ (opcional para usar a regra sem ML)
.\.venv\Scripts\python.exe -m services.modelo

# 7. Iniciar a API; mantenha este terminal aberto
.\.venv\Scripts\python.exe -m uvicorn src.main:app --reload
```

Em outro terminal PowerShell, na raiz do projeto, valide a API e inicie o frontend:

```powershell
# Verificar a API
Invoke-RestMethod http://127.0.0.1:8000/health

# Instalar e iniciar o frontend React + Vite
Set-Location frontend
Copy-Item .env.example .env
npm ci
npm run dev
```

Abra `http://localhost:5173`. O `.env` do frontend aponta por padrão para `http://127.0.0.1:8000`, origem já permitida pela configuração CORS local.

Para o dashboard Streamlit, em um terceiro terminal na raiz, execute `.\.venv\Scripts\python.exe -m streamlit run dashboard/app.py` e acesse `http://localhost:8501`.

Para exercitar o fluxo contínuo do simulador pela API, em outro terminal na raiz:

```powershell
Set-Location mock
..\.venv\Scripts\python.exe simulator.py --modo stream --n 0 --intervalo 1 --api http://127.0.0.1:8000
```

Interrompa o stream com `Ctrl+C`. Para executar as suítes Python, volte à raiz do projeto e rode:

```powershell
.\.venv\Scripts\python.exe -m unittest services.test_regras services.test_modelo src.test_api dashboard.test_dashboard -v
Set-Location mock
..\.venv\Scripts\python.exe -m unittest test_mock test_leitor -v
```

**Validação realizada nesta auditoria:** instalação de `requirements.txt` em venv temporário; 62 testes principais aprovados; 15 testes de mock/leitor aprovados; geração de 3.000 leituras pela CLI; `npm ci` e `npm run build` aprovados. Não foi feita validação de clone limpo, execução live do Uvicorn ou navegação manual no browser.