# 🐴 Observatório de Saúde Equina

> **Pipeline de Engenharia de Dados aplicado à saúde clínica equina.**  
> Da ingestão bruta ao cockpit executivo — com contratos de dados, quarentena rastreável e suporte à decisão veterinária.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.x-150458?style=flat-square&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Pandera](https://img.shields.io/badge/Data%20Contracts-Pandera-orange?style=flat-square)](https://pandera.readthedocs.io/)
[![DuckDB](https://img.shields.io/badge/DuckDB-Analytics-yellow?style=flat-square&logo=duckdb&logoColor=black)](https://duckdb.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Pytest](https://img.shields.io/badge/Testes-pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white)](https://pytest.org/)
[![Status](https://img.shields.io/badge/Status-Produção%20Local-2ea44f?style=flat-square)]()

---

## O Problema

Um cavalo com cólica aguda tem entre **1 e 4 horas** para a decisão cirúrgica ser tomada.

Depois dessa janela, a mortalidade sobe de ~25% para mais de 60%.

Na maioria dos centros equestres, esse diagnóstico depende da experiência individual do veterinário de plantão — sem histórico estruturado, sem rastreabilidade de sinais vitais e sem referência epidemiológica para comparação.

Este projeto constrói a base de dados que torna essa decisão mais informada.

---

## O que este pipeline responde

| Pergunta clínica | Onde está a resposta |
|---|---|
| A frequência cardíaca na admissão já indica risco cirúrgico? | Gold → `tachycardia_triage` → Zona 2 do cockpit |
| Qual o histórico de sobrevivência com e sem cirurgia? | Gold → `surgical_decision` → Zona 3 do cockpit |
| Os dados coletados atendem padrões fisiológicos ou têm anomalias? | Silver → `quality_reports/` → Zona 4 do cockpit |

---

## Arquitetura
*Fonte: UCI Horse Colic Dataset (368 casos clínicos reais, 1989)*

```text
┌─────────────────────────────────────────────────────────────┐
│  BRONZE — Ingestão imutável                                 │
│  horse-colic.data + horse-colic.test → armazenamento bruto  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  SILVER — Contrato de Dados (Pandera)                       │
│  Limpeza · Tipagem · Tradução semântica UCI                 │
│  Aprovados → equine_cases + clinical_measures (Parquet)     │
│  Rejeitados → quarantine/ com _rejection_reason             │
│  Saída → quality_report_YYYYMMDD.json                       │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  GOLD — Indicadores Clínicos (DuckDB + SQL)                 │
│  tachycardia_triage · surgical_decision · pain_analysis     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
         Cockpit Executivo (Streamlit + Plotly)
```

---

## O que representa uma linha de cada tabela?
* **Camada Bronze (`horse-colic.data` / `horse-colic.test`):** Cada linha representa o registro bruto original de um caso clínico de cólica equina coletado em campo (1989), contendo campos delimitados por espaço/vírgula com códigos clínicos e valores ausentes (`?`).
* **Camada Silver (`equine_cases.parquet` / `clinical_measures.parquet`):** Cada linha representa um caso clínico validado e limpo de um cavalo, com tipagem corrigida, chaves primárias (`case_id`) geradas e semântica de desfechos traduzida.
* **Camada Gold (`tachycardia_triage.parquet`, `surgical_decision.parquet`, etc.):** Cada linha representa uma agregação analítica por métricas de triagem, desfechos de sobrevivência ou faixas de frequência cardíaca para suporte à decisão veterinária.

---

## Contratos de Dados — As 3 Regras Clínicas Críticas

A camada Silver valida cada registro contra regras fisiológicas reais, não apenas tipos de dados:

| Variável | Regra no Contrato | Fundamento Clínico |
|---|---|---|
| `pulse` | 20–300 bpm · Alerta acima de 60 | FC > 60 bpm = limiar de indicação cirúrgica |
| `packed_cell_volume` | 20–75% · Alerta acima de 50% | PCV elevado = hemoconcentração / choque iminente |
| `pain` | Validação dupla: código UCI (1–5) → semântica (`alert` … `continuous_severe_pain`) | Scores 4–5 correlacionam com 3× mais indicações cirúrgicas |

Registros que violam qualquer regra são isolados em `data/silver/quarantine/` com o motivo exato da falha — rastreabilidade completa a cada execução.

---

## Cockpit Executivo

```text
├── Zona 1 ── KPIs: Mortalidade Geral · Taxa Cirúrgica · FC Crítica ─────────┐
├── Zona 2 ── Triagem por FC: semáforo clínico (verde → vermelho) ────────────┤
├── Zona 3 ── Perfil Cirúrgico + Nota de viés de seleção ─────────────────────┤
└── Zona 4 ── Observabilidade: quality_report.json do último run ─────────────┘
```

---

## Como executar

Você pode rodar todo o pipeline de dados (testes + Bronze + Silver + Gold) e iniciar o painel interativo de diferentes formas, dependendo da sua preferência:

### Opção A: No Windows (Com duplo clique)
Dê um duplo clique no arquivo **`executar.bat`** diretamente no Explorador de Arquivos do Windows. Ele ativará o ambiente virtual e rodará tudo automaticamente.

### Opção B: Via Terminal (Comando unificado)
No terminal com o ambiente virtual ativado:
```bash
# Executa o pipeline completo com pausa para conferência e abre o dashboard
python desafio_um.py
```

Opção C: Execução Manual Isolada (Passo a passo)
Se preferir rodar cada etapa de forma isolada:

Bash
# 1. Executar testes unitários
pytest tests/ -v --tb=short

# 2. Ingestão da Camada Bronze
python src/ingestion/download_uci_data.py

# 3. Processamento e validação da Camada Silver
python src/transformations/process_silver.py

# 4. Construção das tabelas da Camada Gold
python src/gold/build_gold.py

# 5. Iniciar o Cockpit Executivo
streamlit run app.py

---

## Estrutura do repositório

```
Desafio1/
│
├── data/
│   ├── bronze/
│   │   ├── horse-colic.data            # Dados brutos de treino (UCI)
│   │   └── horse-colic.test            # Dados brutos de teste (UCI)
│   ├── silver/
│   │   ├── schemas.py                  # Contratos Pandera (regras fisiológicas)
│   │   ├── validate.py                 # Motor de quarentena (lazy=True)
│   │   ├── quarantine/                 # Registros rejeitados com _rejection_reason
│   │   └── quality_reports/            # quality_report_YYYYMMDD.json por execução
│   └── gold/
│       ├── 01_outcomes_distribution.sql     # Distribuição de desfechos clínicos
│       ├── 02_survival_by_lesion_type.sql   # Sobrevivência por tipo de lesão
│       ├── 03_surgery_vs_outcome.sql        # Cirurgia × desfecho comparativo
│       ├── 04_vital_signs_by_outcome.sql    # Sinais vitais agregados por desfecho
│       └── 05_pain_level_analysis.sql       # Dor na triagem × resultado final
│
├── docs/                               # Documentação técnica e diagramas
│
├── sql/
│   └── gold/                           # Versão alternativa/versionada das queries Gold
│
├── src/
│   ├── gold/
│   │   └── build_gold.py               # Constrói tabelas Parquet via DuckDB
│   ├── ingestion/
│   │   └── download_uci_data.py        # Download automatizado do dataset UCI
│   └── transformations/
│       └── process_silver.py           # Transformações e mapeamento Bronze → Silver
│
├── tests/
│   └── unit/
│       └── test_silver_transformations.py  # Suíte pytest em memória
│
├── app.py                              # Cockpit Executivo (Streamlit + Plotly)
├── desafio_um.py                       # Automação completa do pipeline (Python)
├── executar.bat                        # Atalho para Windows (duplo clique)
├── Makefile                            # Automação via make (Linux/macOS)
├── pipeline_medallion_guia.html        # Guia visual interativo e simulador do fluxo
├── README.md
└── requirements.txt


```

---

> 📊 **Guia Interativo de Arquitetura e Execução:** 
> Explore o fluxo completo do pipeline, as regras de cada camada e um simulador de falhas/testes acessando o guia visual:
> * **Online (via navegador):** [Abrir Guia Interativo Medallion](https://github.com/alesina78/desafio_eng_jr/blob/master/pipeline_medallion_guia.html)
> * **Localmente:** Dê um duplo clique no arquivo `pipeline_medallion_guia.html` na raiz deste repositório.

---

## 🤖 Relato de Interação com a IA (Erros e Correções)

Como todo projeto assistido por IA, houve momentos em que a ferramenta assumiu premissas incorretas que exigiram validação técnica rigorosa e testes práticos:

* **1. Divergência na Contagem de Registros (Quarentena):** 
  * *O que a IA assumiu:* Que os 368 registros brutos passariam direto para as tabelas finais da Silver.
  * *Como descobri testando:* Ao rodar o pipeline, notei que a Silver gerou 366 linhas em vez de 368. O relatório JSON (`quality_report.json`) revelou que 2 registros haviam sido isolados em quarentena por violarem os limites fisiológicos de dor e frequência cardíaca. Isso validou o motor de quarentena.
* **2. Tratamento de Valores Nulos Mascarados na Fonte UCI (`?`):**
  * *O que a IA assumiu:* Que colunas como `pulse` e `packed_cell_volume` eram puramente numéricas desde a leitura inicial.
  * *Como descobri testando:* O DuckDB e os testes unitários quebraram com erros de conversão de tipo (`Type mismatch`). Identifiquei que a fonte original usa `?` para nulos, exigindo a conversão explícita com `pd.to_numeric(errors='coerce')` antes das validações do Pandera.
* **3. Incompatibilidade de Tipos e Parâmetros Gráficos (Streamlit/Plotly):**
  * *O que a IA assumiu:* Propriedades descontinuadas de layout (como o antigo `use_container_width`).
  * *Como descobri testando:* O terminal exibiu avisos de depreciação e falhas visuais. Corrigi inspecionando os logs de execução e atualizando para os parâmetros modernos.


---

## Testes

```bash
pytest tests/unit/ -v
```
*Suíte unitária em memória — sem dependências externas, sem banco de dados.*

---

## Limitações e próximos passos

Este projeto não é um modelo preditivo. É um sistema de apoio à decisão baseado em evidência histórica, com as limitações que isso implica:

* **Dataset de 1989 com 368 casos** — não representa distribuições clínicas atuais.
* **Variáveis com até 29% de nulos** na fonte original — tratados e documentados, não ignorados.
* **Comparação cirúrgica sujeita a viés de seleção** (casos mais graves são operados) — anotado no cockpit.
* **Próximo passo natural:** integração com dados longitudinais de um centro equestre real.

---

## Autor

**Alessandro Lesina Giordano**  
Senior Data Engineer & Analytics Specialist | 25+ anos em TI Corporativa  

[![GitHub](https://img.shields.io/badge/GitHub-alesina78-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/alesina78)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-alessandrolesina-0077B5?style=flat-square&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/alessandrolesina/)
[![Email](https://img.shields.io/badge/Email-giordano.dba%40gmail.com-D14836?style=flat-square&logo=gmail&logoColor=white)](mailto:giordano.dba@gmail.com)

> *Dataset de referência: UCI Machine Learning Repository — Horse Colic Dataset, distribuído sob licença Creative Commons Attribution 4.0 International (CC BY 4.0).*