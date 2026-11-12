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

Você pode rodar todo o pipeline de dados (testes + Bronze + Silver + Gold) e iniciar o painel interativo com um único comando:

```bash
# Executa o pipeline completo com pausa para conferência e abre o dashboard
python desafio_um.py
```

Ou, se preferir executar as etapas de forma isolada manualmente:

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
│   │   ├── horse-colic.data          # Dados brutos de treino (UCI)
│   │   └── horse-colic.test          # Dados brutos de teste (UCI)
│   ├── silver/
│   │   ├── schemas.py                # Contratos Pandera (regras fisiológicas)
│   │   ├── validate.py               # Motor de quarentena (lazy=True)
│   │   ├── quarantine/               # Registros rejeitados com _rejection_reason
│   │   └── quality_reports/          # quality_report_YYYYMMDD.json por execução
│   └── gold/
│       ├── 01_outcomes_distribution.sql   # Distribuição de desfechos clínicos
│       ├── 02_survival_by_lesion_type.sql # Sobrevivência por tipo de lesão
│       ├── 03_surgery_vs_outcome.sql      # Cirurgia × desfecho comparativo
│       ├── 04_vital_signs_by_outcome.sql  # Sinais vitais agregados por desfecho
│       └── 05_pain_level_analysis.sql     # Dor na triagem × resultado final
│
├── docs/                             # Documentação técnica e diagramas
│
├── sql/
│   └── gold/                         # Versão alternativa/versionada das queries Gold
│
├── src/
│   ├── gold/
│   │   └── build_gold.py             # Constrói tabelas Parquet via DuckDB
│   ├── ingestion/
│   │   └── download_uci_data.py      # Download automatizado do dataset UCI
│   └── transformations/
│       └── process_silver.py         # Transformações e mapeamento Bronze → Silver
│
├── tests/
│   └── unit/
│       └── test_silver_transformations.py  # Suíte pytest em memória
│
├── app.py                            # Cockpit Executivo (Streamlit + Plotly)
├── Makefile                          # make pipeline — execução em 1 comando
├── README.md
└── requirements.txt

```

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