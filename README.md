# 🐎 GATE4 Equine Health Intelligence

> **Plataforma de Engenharia de Dados & Analytics** aplicada ao monitoramento clínico e à gestão de saúde em centros equestres.  
> Pipeline end-to-end: ingestão de dados brutos (UCI Horse Colic) → camadas Medallion (Bronze/Silver/Gold) → validações com Pytest → Analytics em SQL Puro.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.x-150458?style=flat-square&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Pytest](https://img.shields.io/badge/Testes-pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white)](https://pytest.org/)
[![Status](https://img.shields.io/badge/Status-Ativo-2ea44f?style=flat-square)]()

---

## 🎯 O Problema de Negócio

Centros equestres, haras e clínicas veterinárias lidam frequentemente com dados fragmentados de ocorrências de saúde animal, registros de exames e desfechos de tratamentos. O resultado é a dificuldade de identificar padrões clínicos e avaliar o sucesso de intervenções médicas em casos críticos.

Este projeto constrói a **espinha dorsal de dados** para análise de atendimentos veterinários de cólica equina — aplicando engenharia de dados moderna sobre dados reais de saúde animal para apoiar gestores e profissionais veterinários na tomada de decisão baseada em evidências.

**Perguntas que o pipeline responde:**
- Qual é a taxa de sobrevivência dos animais conforme o tipo de lesão diagnosticada?
- Qual é o impacto da intervenção cirúrgica no desfecho de casos de cólica severa?
- Como o nível de dor e os sinais vitais iniciais se correlacionam com a taxa de mortalidade e eutanásia?
- Qual é o perfil clínico associado a cada desfecho hospitalar (`lived`, `died`, `euthanized`)?

---

## 🏗️ Arquitetura Medallion

```
┌─────────────────────────────────────────────────────────────┐
│               GATE4 Equine Health Intelligence              │
├───────────────────┬───────────────────┬─────────────────────┤
│     BRONZE        │      SILVER       │        GOLD         │
│  Arquivos brutos  │  Dados limpos &   │ Indicadores SQL     │
│  (.data / .test)  │   Normalizados    │  independentes      │
└───────────────────┴───────────────────┴─────────────────────┘
```

**Modelo de Dados Relacional:** Os registros brutos são estruturados em duas tabelas centrais na camada Silver, garantindo integridade referencial por meio de um `JOIN` relacional limpo baseado na chave `case_id`.

---

## 📦 Estruturação das Tabelas (Camada Silver)

| Tabela | Granularidade | Descrição das Atributos Principais |
|---|---|---|
| **`equine_cases`** | Uma linha por atendimento clínico | `case_id` (PK), `hospital_number`, `age`, `surgery`, `lesion_type`, `surgical_lesion`, `outcome` |
| **`clinical_measures`** | Uma linha de medição por atendimento | `case_id` (FK), `rectal_temperature`, `pulse`, `respiratory_rate`, `mucous_membranes`, `capillary_refill_time`, `pain`, `peristalsis`, `abdominal_distension` |

---

## 📊 Indicadores da Camada Gold (Arquivos `.sql` Independentes)

Cada indicador analítico é gerado diretamente por um arquivo SQL dedicado na camada de consumo:

1. **`01_outcomes_distribution.sql`** — Distribuição percentual dos desfechos clínicos (sobreviveu, morreu, eutanásia).
2. **`02_survival_by_lesion_type.sql`** — Taxa de sobrevivência cruzada por tipo de lesão diagnosticada.
3. **`03_surgery_vs_outcome.sql`** — Análise comparativa de desfechos entre casos que exigiram cirurgia e tratamento conservador.
4. **`04_vital_signs_by_outcome.sql`** — Agregação e variação de sinais vitais críticos (como pulso e temperatura) agrupados por desfecho.
5. **`05_pain_level_analysis.sql`** — Correlação entre o nível de dor registrado na triagem e o resultado final do atendimento.

---

## 🧪 Testes Automatizados (Pytest)

O projeto conta com uma suíte de testes unitários desenvolvida em `pytest`, simulando DataFrames e estruturas de dados em memória para validar as regras de transformação, tipagem e integridade referencial **sem abrir o banco de dados do projeto**, atendendo rigorosamente aos critérios acadêmicos do desafio.

```bash
pytest tests/unit/
```

---

## ▶️ Como Rodar o Projeto do Zero

### Pré-requisitos
* Python 3.10+ instalado.
* Git instalado.

### Passo a passo no terminal:

```bash
# 1. Clonar o repositório
git clone https://github.com/alesina78/gate4-equine-health.git
cd gate4-equine-health

# 2. Criar e ativar o ambiente virtual
python -m venv .venv
# Git Bash:
source .venv/Scripts/activate
# PowerShell:
# .\.venv\Scripts\activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Executar os testes unitários
pytest tests/unit/
```

---

## 📁 Estrutura do Repositório

```
gate4-equine-health/
│
├── data/
│   ├── bronze/          # Arquivos brutos originais (.data / .test)
│   ├── silver/          # Dados tratados, tipados e separados em tabelas
│   └── gold/            # Tabelas e visões analíticas finais
│
├── src/
│   ├── ingestion/       # Scripts de extração e salvamento em Bronze
│   ├── transformations/ # Lógicas de limpeza, tipagem e normalização (Silver)
│   └── database/        # Configuração de conexão e persistência local
│
├── sql/
│   └── gold/            # Arquivos .sql independentes para cada indicador
│
├── tests/
│   └── unit/            # Testes unitários com pytest (dados em memória)
│
├── docs/                # Documentação técnica e dicionário de dados
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🤖 Seção de Registro de IA

*(Espaço reservado para documentar os momentos em que a IA cometeu suposições incorretas, desvios de escopo ou falhas de lógica durante o desenvolvimento, detalhando a conferência de linhas e as correções aplicadas pelo autor).*

---

## 👤 Autor

**Alessandro Lesina Giordano**  
Senior Data Engineer & Analytics Specialist | 25+ anos em TI Corporativa  

[![GitHub](https://img.shields.io/badge/GitHub-alesina78-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/alesina78)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-alessandrolesina-0077B5?style=flat-square&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/alessandrolesina/)
[![Email](https://img.shields.io/badge/Email-giordano.dba%40gmail.com-D14836?style=flat-square&logo=gmail&logoColor=white)](mailto:giordano.dba@gmail.com)

> *Dataset de referência: UCI Machine Learning Repository — Horse Colic Dataset, distribuído sob licença Creative Commons Attribution 4.0 International (CC BY 4.0).*