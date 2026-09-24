# 🛠️ Sistema Inteligente de Diagnóstico Preditivo de Falhas Mecânicas

> **Empresa:** ArcelorMittal / Tuper  

---

## Equipe
* **Ederlane Ciribelle Silva Fernandes**
* **Iran Andrei da Costa**
* **Paulo Ricardo Wosniak Soares**

---

## Visão Geral do Projeto
O **Sistema Inteligente de Diagnóstico Preditivo** é uma solução voltada para a indústria com o objetivo de otimizar rotinas de manutenção preditiva e evitar paradas não planejadas em linhas de produção. 

O sistema recebe e processa dados históricos de vibração e rotação capturados de máquinas industriais, aplicando análises estatísticas avançadas e técnicas de Inteligência Artificial para identificar comportamentos anômalos que indicam desgaste mecânico ou iminência de falhas. Os resultados são expostos em um painel web intuitivo em tempo real.

---

## Objetivo Geral
Desenvolver uma aplicação capaz de analisar dados de sensores de vibração, detectar anomalias comportamentais em equipamentos industriais e emitir alertas preditivos categorizados, auxiliando na redução de custos e na prevenção de falhas graves em componentes mecânicos.

---

## Escopo do MVP (42 Horas)

O desenvolvimento do Produto Mínimo Viável (MVP) está dividido em 4 etapas fundamentais:

1. **Ingestão de Dados:** Entrada de dados históricos/sintéticos de sensores disponibilizados em formatos `CSV` ou `JSON`.
2. **Processamento & Análise Estatística:** Módulo em Python focado na extração de atributos e cálculo de indicadores chaves:
   * **RMS** (*Root Mean Square*)
   * **Assimetria** (*Skewness*)
   * **Curtose** (*Kurtosis*)
3. **Detecção de Anomalias com IA:** Aplicação do algoritmo não supervisionado **Isolation Forest**, capaz de reconhecer padrões fora do espectro normal sem a necessidade prévia de rotulagem de todas as falhas existentes.
4. **Dashboard Web:** Interface interativa para monitoramento contínuo da saúde dos equipamentos, exibindo status por código de cores:
   * 🟢 **Normal:** Funcionamento dentro dos parâmetros padrão.
   * 🟡 **Atenção:** Desvios estatísticos detectados (possível desgaste).
   * 🔴 **Crítico:** Forte indicativo de anomalia ou risco de falha iminente.

---

## Tecnologias Utilizadas
* **Linguagem Principal:** Python
* **Análise & ML:** Pandas, NumPy, Scikit-learn (`Isolation Forest`)
* **Visualização & Dashboard:** Streamlit / Dash / Framework Web (Backend & Frontend)
* **Formatos de Dados:** CSV / JSON
---

## Licença
Projeto desenvolvido para fins acadêmicos e de aplicação prática no contexto da ArcelorMittal / Tuper.
