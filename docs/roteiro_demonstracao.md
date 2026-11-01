# Roteiro de demonstração — Checkpoint 2

Demonstração ao vivo do fluxo completo: **simulador → API → banco → painel**, em 6 a 8 minutos.
Todos os integrantes devem saber explicar cada parte (a ordem de quem fala abaixo é só uma sugestão).

---

## Antes da aula (uma vez)

Na pasta do projeto, com o `venv` ativado:

```bash
pip install -r requirements.txt
cd mock && python simulator.py && cd ..     # 3000 leituras históricas (semente 42)
python -m services.modelo                   # treina o Isolation Forest
python -m unittest services.test_regras services.test_modelo src.test_api dashboard.test_dashboard
```

Confira que os testes passam e que existe `modelos_treinados/isolation_forest.joblib`.

**Para a tela começar vazia** (fica mais fácil ver os dados chegando): apague `mock/data/vibracao.db` antes de subir a API. Ela recria as tabelas sozinha. O modelo já treinado continua valendo, desde que o simulador use a mesma semente (42, o padrão).

---

## Na hora: três terminais

| Terminal | Comando | Deixar aberto em |
|---|---|---|
| 1. API | `uvicorn src.main:app` | — |
| 2. Painel | `streamlit run dashboard/app.py` | navegador em `http://localhost:8501` |
| 3. Simulador | `cd mock` e depois `python simulator.py --modo stream --n 0 --intervalo 1 --anomalias 0.3 --api http://127.0.0.1:8000` | terminal visível ao lado do navegador |

Use `127.0.0.1` e não `localhost` no simulador: no Windows, `localhost` deixa cada envio ~2 s mais lento.
`--anomalias 0.3` faz as falhas aparecerem mais rápido; no uso normal o padrão é 0.1.

---

## Roteiro (6 a 8 min)

**1. O problema e a regra — 1 min** *(pessoa A)*
- Paradas não planejadas por desgaste de motores e compressores; vibração denuncia o desgaste antes da quebra.
- Mostrar a regra no terminal: `python -m services.regras` (caso normal, crítico e erro de entrada).
- Critério: ISO 10816 adaptada. RMS ≥ 4,5 mm/s ou curtose ≥ 4 → ATENÇÃO; RMS ≥ 7,1 ou curtose ≥ 8 → CRÍTICO.

**2. A API — 1 min** *(pessoa B)*
- Abrir `http://127.0.0.1:8000/docs`, `POST /api/dados` → Try it out.
- Enviar uma leitura válida (resposta 201 com status, cor, motivos, modelo e alerta).
- Enviar `"rms": -1` (resposta 422 com a mensagem em português).
- Ponto a destacar: quem chama a API **não** manda o status; ele é calculado pela regra no backend.

**3. Fluxo ponta a ponta — 3 min** *(pessoa C)*
- Ligar o simulador (terminal 3). Mostrar no terminal cada leitura indo para a API e o status que volta.
- No painel: cartões mudando de cor, a lista de alertas crescendo, o gráfico com os limiares tracejados.
- **Destaque principal:** quando aparecer `modelo:anômalo` no terminal com o status ainda `NORMAL`, mostrar no painel o aviso "⚠ MODELO: PADRÃO ANÔMALO" e, no gráfico, os anéis antes da linha de atenção. É o modelo antecipando a degradação.
- Clicar em **Reconhecer** num alerta.

**4. Robustez — 1 min** *(pessoa A)*
- Parar a API (Ctrl+C no terminal 1).
- Painel: aviso vermelho "Sem comunicação com a API desde …", últimos dados esmaecidos na tela.
- Simulador: "[erro] API indisponível … tentando de novo".
- Subir a API de novo: tudo volta sozinho.

**5. Resultados e IA — 1 min** *(pessoa B)*
- Avaliação em dados que o modelo não viu: Isolation Forest pega 94% das anomalias (precisão 0,77); a regra pega 62% (precisão 1,0).
- Por isso: a regra decide o semáforo e os alertas; o modelo é um aviso antecipado.
- 77 testes automáticos; `AI_LOG.md` com o que a IA errou e o que corrigimos.

---

## Perguntas prováveis

| Pergunta | Resposta curta |
|---|---|
| Por que Isolation Forest? | É não supervisionado: aprende o "normal" de cada sensor sem precisar de falhas rotuladas, que a planta não tem. |
| Por que um modelo por sensor? | Cada máquina e posição tem seu nível normal de vibração; um modelo único confundiria um compressor com um motor. |
| Como evitaram vazamento de dados? | `anomalia_real` e `tipo_anomalia` (o gabarito do simulador) nunca entram no treino; servem só para avaliar. |
| Como avaliaram? | Divisão temporal: os primeiros 70% de cada sensor treinam e os 30% finais testam, como aconteceria na prática. |
| Por que o modelo não muda a cor do cartão? | Precisão de 0,77: cerca de 1 em cada 4 avisos é falso. Semáforo com alarme falso faz o operador desconfiar do painel. |
| O que é curtose? | Mede picos e impactos no sinal (normal ≈ 3). Sobe com defeito de rolamento, mesmo com RMS baixo. |
| Precisa de CORS com Streamlit? | Não, o Streamlit chama a API pelo servidor Python. Foi configurado para qualquer front que rode no navegador. |
| E com dados reais da Tuper? | Recalibrar os limiares da regra e retreinar o modelo com o histórico real (`python -m services.modelo`). |
| O que fica fora do MVP? | Conexão direta com CLP/sensores (OPC-UA/MQTT), envio de SMS/WhatsApp, FFT completa e autenticação. |

---

## Se algo der errado

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| Painel com "API indisponível" desde o início | API não está no ar | Subir o terminal 1 e recarregar o painel |
| Simulador muito lento (~2 s por leitura) | Usou `localhost` | Usar `--api http://127.0.0.1:8000` |
| Caixa de diagnóstico diz "modelo não treinado" | Falta o arquivo do modelo | `python -m services.modelo` e reiniciar a API |
| Modelo marca máquinas normais como anômalas | Simulador com semente diferente da do treino | Rodar o simulador sem `--seed` (padrão 42) |
| Gráfico com um "salto" de dias | Histórico antigo misturado com leituras novas | Apagar `mock/data/vibracao.db` antes de subir a API |
| Porta 8000 ou 8501 ocupada | Outra execução ainda aberta | Fechar o terminal antigo ou usar `--port` |
