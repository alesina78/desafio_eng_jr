"""
Data Contract v1.0.0 — Horse Colic Observatory (Camada Silver)
==============================================================

Este módulo define os contratos de dados (Data Contracts) utilizando a biblioteca
`pandera` para validar e documentar a qualidade dos dados clínicos equinos na
camada Silver.

Arquitetura & Fluxo:
    - Origem: UCI Machine Learning Repository (Horse Colic Dataset).
    - Camada Bronze: Dados brutos com códigos numéricos originais.
    - Camada Silver (Este Contrato): Dados tipados, validados fisiologicamente
      e traduzidos de códigos numéricos para semântica clínica legível.

Referências Clínicas:
    - Robinson, N. E. (2003). *Current Therapy in Equine Medicine* (5th ed.).
    - UCI Machine Learning Repository: Horse Colic Data Set Documentation.

Autor: Engenharia de Dados / Horse Colic Observatory
Versão: 1.0.0
"""

from typing import Final
import pandera as pa

# ==============================================================================
# CONSTANTES DE DOMÍNIO E METADADOS GLOBAIS
# ==============================================================================
CONTRACT_VERSION: Final[str] = "1.0.0"

VALID_PAIN_LEVELS: Final[list[str]] = [
    "alert",                    # Código UCI 1: Sem dor, animal alerta e responsivo
    "depressed",                # Código UCI 2: Animal deprimido/apático
    "intermittent_mild_pain",   # Código UCI 3: Dor leve intermitente
    "intermittent_severe_pain", # Código UCI 4: Dor grave intermitente
    "continuous_severe_pain",   # Código UCI 5: Dor grave contínua (alta urgência)
]

VALID_OUTCOMES: Final[list[str]] = [
    "lived",          # Sobreviveu ao episódio de cólica
    "died",           # Veio a óbito naturalmente/complicações
    "was euthanized", # Submetido à eutanásia devido ao prognóstico
]


# ==============================================================================
# DEFINIÇÃO DE REGRAS CLÍNICAS E COLUNAS REUTILIZÁVEIS (COLUMN CHECKS)
# ==============================================================================

# ── Regra Clínica #1: Frequência Cardíaca (Pulse) ────────────────────────────
# Justificativa Médica: A taquicardia em equinos é um dos indicadores mais
# confiáveis de dor visceral, endotoxemia e comprometimento hemodinâmico.
# Limiar crítico: > 60 bpm indica provável emergência cirúrgica.
PULSE_CHECK: pa.Column = pa.Column(
    dtype=float,
    checks=[
        pa.Check.in_range(
            min_value=20.0,
            max_value=300.0,
            error="FC fora do intervalo fisiológico equino plausível (20-300 bpm).",
        ),
        pa.Check(
            check_fn=lambda s: s.isna() | (s > 0),
            error="FC não pode ser zero ou negativa (verificar falha de sensor/digitação).",
        ),
    ],
    nullable=True,
    description=(
        "Frequência cardíaca medida em batimentos por minuto (bpm). "
        "Faixa normal em repouso: 28-44 bpm. "
        "Alerta clínico/cirúrgico: > 60 bpm. Estado crítico: > 80 bpm."
    ),
    metadata={
        "clinical_rule": "tachycardia_triage",
        "unit": "bpm",
        "source_uci_attribute": "4 (pulse)",
        "version": CONTRACT_VERSION,
    },
)

# ── Regra Clínica #2: Hematócrito (Packed Cell Volume - PCV) ─────────────────
# Justificativa Médica: O PCV mede a porcentagem de glóbulos vermelhos no sangue.
# Valores > 50% indicam hemoconcentração severa por perda de fluidos para o
# lúmen intestinal, sinalizando choque hipovolêmico iminente.
PCV_CHECK: pa.Column = pa.Column(
    dtype=float,
    checks=[
        pa.Check.in_range(
            min_value=20.0,
            max_value=75.0,
            error="PCV fora do intervalo fisiológico equino (20-75%).",
        ),
        pa.Check(
            check_fn=lambda s: s.isna() | (s <= 65.0),
            error=(
                "PCV > 65%: valor clinicamente extremo/improvável. "
                "Verificar erro de escala (% vs fração decimal) ou hemoconcentração crítica (> 50%)."
            ),
        ),
    ],
    nullable=True,
    description=(
        "Volume Globular / Hematócrito (PCV) expresso em porcentagem (%). "
        "Faixa normal equina: 32-48%. "
        "Alerta de desidratação: > 45%. Risco de choque hipovolêmico: > 50%."
    ),
    metadata={
        "clinical_rule": "hypovolemic_shock_marker",
        "unit": "percentage (%)",
        "source_uci_attribute": "19 (packed cell volume)",
        "version": CONTRACT_VERSION,
    },
)

# ── Regra Clínica #3: Nível de Dor (Pain) ────────────────────────────────────
# Justificativa Médica: Avaliação subjetiva do comportamento álgico do equino.
# Na camada Silver, os códigos numéricos (1 a 5) da Bronze devem estar
# obrigatoriamente traduzidos para strings semânticas padronizadas.
PAIN_SILVER_CHECK: pa.Column = pa.Column(
    dtype=str,
    checks=[
        pa.Check.isin(
            allowed_values=VALID_PAIN_LEVELS,
            error=(
                "Valor de 'pain' inválido na camada Silver. Deve ser um dos 5 valores "
                "semânticos UCI. Verifique o pipeline de transformação Bronze -> Silver."
            ),
        )
    ],
    nullable=True,
    description=(
        "Classificação semântica do nível de dor (mapeado dos códigos UCI 1 a 5). "
        "Correlação clínica: níveis 'intermittent_severe_pain' (4) e "
        "'continuous_severe_pain' (5) aumentam em 3x a probabilidade de intervenção cirúrgica."
    ),
    metadata={
        "clinical_rule": "pain_surgical_correlation",
        "transformation": "uci_code_to_semantic_label",
        "source_uci_attribute": "11 (pain)",
        "version": CONTRACT_VERSION,
    },
)


# ==============================================================================
# SCHEMAS OFICIAIS DA CAMADA SILVER (DATAFRAME SCHEMAS)
# ==============================================================================

EQUINE_SCHEMA: pa.DataFrameSchema = pa.DataFrameSchema(
    columns={
        "case_id": pa.Column(
            dtype=int,
            checks=pa.Check.gt(0, error="O ID do caso deve ser um inteiro positivo."),
            nullable=False,
            unique=True,  # Garante integridade de chave primária na tabela de casos
            description="Chave primária única identificando o atendimento/episódio clínico.",
        ),
        "hospital_number": pa.Column(
            dtype=float,
            nullable=True,
            description=(
                "Identificador numérico do prontuário do cavalo no hospital. "
                "Nota: Um mesmo cavalo pode ter múltiplos 'case_id' se retornar."
            ),
        ),
        "age": pa.Column(
            dtype=float,
            nullable=True,
            description="Faixa etária categorizada do equino (1 = Adulto, 2 = Jovem < 6 meses).",
        ),
        "surgery": pa.Column(
            dtype=float,
            nullable=True,
            description="Indica se o animal passou por cirurgia (1 = Sim, 2 = Não).",
        ),
        "surgical_lesion": pa.Column(
            dtype=float,
            nullable=True,
            description="Diagnóstico retrospectivo confirmando se a lesão exigia cirurgia (1 = Sim, 2 = Não).",
        ),
        "outcome_label": pa.Column(
            dtype=str,
            checks=pa.Check.isin(
                allowed_values=VALID_OUTCOMES,
                error="Desfecho clínico inválido. Valores esperados: 'lived', 'died', 'was euthanized'.",
            ),
            nullable=True,
            description="Desfecho clínico final do paciente após o tratamento.",
        ),
    },
    name="equine_cases_silver_v1",
    description="Tabela dimensão/entidade contendo dados cadastrais, cirúrgicos e desfecho dos equinos.",
    strict=False,  # Permite colunas adicionais de auditoria (ex: _ingested_at) sem quebrar o contrato
    coerce=True,   # Tenta converter tipos compatíveis (ex: int para float) antes de validar
)

CLINICAL_SCHEMA: pa.DataFrameSchema = pa.DataFrameSchema(
    columns={
        "case_id": pa.Column(
            dtype=int,
            checks=pa.Check.gt(0, error="O ID do caso deve ser um inteiro positivo."),
            nullable=False,
            description="Chave estrangeira (FK) referenciando 'equine_cases_silver_v1.case_id'.",
        ),
        "rectal_temperature": pa.Column(
            dtype=float,
            checks=pa.Check.in_range(
                min_value=35.0,
                max_value=43.0,
                error="Temperatura retal fora dos limites compatíveis com a vida (35°C - 43°C).",
            ),
            nullable=True,
            description=(
                "Temperatura retal em graus Celsius (°C). Normal equino: 37.2°C - 38.3°C. "
                "Hipotermia (< 36.5°C) pode indicar choque circulatório tardio."
            ),
        ),
        "pulse": PULSE_CHECK,
        "respiratory_rate": pa.Column(
            dtype=float,
            checks=pa.Check.in_range(
                min_value=5.0,
                max_value=120.0,
                error="Frequência respiratória fora do intervalo fisiológico (5 - 120 mrpm).",
            ),
            nullable=True,
            description=(
                "Frequência respiratória em movimentos por minuto (mrpm). "
                "Normal equino: 8 - 16 mrpm. Elevações refletem dor ou acidose metabólica."
            ),
        ),
        "pain": PAIN_SILVER_CHECK,
        "packed_cell_volume": PCV_CHECK,
    },
    name="clinical_measures_silver_v1",
    description="Tabela fato contendo os sinais vitais e parâmetros laboratoriais de triagem.",
    strict=False,
    coerce=True,
)
