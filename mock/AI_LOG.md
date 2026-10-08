# AI_LOG — Registro de uso de IA

## Semana — Aula 03: Dados e Mocks Industriais

**Ferramenta:** Claude (Anthropic)

### Onde a IA ajudou
- Propôs o esquema enxuto (4 tabelas: `ativos`, `sensores`, `leituras_brutas`, `alertas`) com DDL em SQLite e restrições CHECK/FK.
- Escreveu `mock/simulator.py` (modos lote e stream), `mock/validar.py` e `mock/test_mock.py`.
- Modelou anomalias fisicamente plausíveis (desbalanceamento, desalinhamento, rolamento, pico isolado, sensor travado) com degradação progressiva.

### Correções feitas durante os testes (ajustes nos dados)
- Anomalia de rolamento saiu com curtose ~3,3 (indistinguível do normal): pulsos longos se sobrepunham. Encurtamos os pulsos e ajustamos a amplitude → curtose média ~5.
- Desalinhamento gerava RMS médio ~2,2 (abaixo do limiar de atenção): aumentamos a amplitude da componente 2x.
- A fração real de anomalias varia por semente (7–10% em vez de exatos 10%), pois os episódios são aleatórios; o teste aceita 5–15%.

### Correções que a equipe fez na mão
- (preencher: ex. ajuste de limiares ao valor real dos sensores da Tuper, nomes de ativos, unidades)

### Observações / riscos
- Dados 100% sintéticos: limiares e distribuições precisam ser calibrados com dados reais da Tuper.
- A regra de limiar deixa passar o início da degradação (severidade baixa) — é aí que o Isolation Forest deve agregar valor.

### Leitura dos dados (`mock/leitor_dados.py`)
- IA ajudou: carregador unificado (SQLite/CSV/JSON), validação com separação de linhas rejeitadas, resumo por sensor e baseline com Isolation Forest (um modelo por sensor).
- Resultado no mock (5000 leituras): Isolation Forest recall ~0,85 / precisão ~0,83; regra de limiar recall ~0,57 / precisão 1,0.
- Correções da equipe: (preencher)
