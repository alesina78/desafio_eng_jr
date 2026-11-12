"""
Camada Gold — Geração das tabelas analíticas clínicas para o Observatório.
Lê os Parquets aprovados da Silver e exporta as visões de negócio.
"""

import logging
from pathlib import Path
import duckdb

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SILVER_DIR = Path("data/silver")
GOLD_DIR = Path("data/gold")
GOLD_DIR.mkdir(parents=True, exist_ok=True)


def build_gold_tables() -> None:
    cases_path = SILVER_DIR / "equine_cases.parquet"
    clinical_path = SILVER_DIR / "clinical_measures.parquet"

    if not cases_path.exists() or not clinical_path.exists():
        logger.error("Arquivos Parquet da Silver não encontrados. Execute o pipeline Silver primeiro.")
        return

    con = duckdb.connect(database=":memory:")

    # 1. Tabela Gold: Triagem por Taquicardia
    query_triage = f"""
    COPY (
        SELECT
            CASE
                WHEN cm.pulse < 44  THEN 'Normal (< 44 bpm)'
                WHEN cm.pulse < 60  THEN 'Alerta (44-60 bpm)'
                WHEN cm.pulse < 80  THEN 'Crítico (60-80 bpm)'
                ELSE                     'Emergência (> 80 bpm)'
            END AS triage_level,
            COUNT(*) AS total_cases,
            ROUND(AVG(CASE WHEN ec.outcome_label IN ('died', 'euthanized') THEN 100.0 ELSE 0.0 END), 1) AS mortality_pct,
            ROUND(AVG(CASE WHEN ec.surgery = 1.0 THEN 100.0 ELSE 0.0 END), 1) AS surgical_rate_pct
        FROM read_parquet('{cases_path}') ec
        JOIN read_parquet('{clinical_path}') cm ON ec.case_id = cm.case_id
        WHERE cm.pulse IS NOT NULL
        GROUP BY 1
        ORDER BY mortality_pct ASC
    ) TO '{GOLD_DIR / "tachycardia_triage.parquet"}' (FORMAT PARQUET);
    """
    con.execute(query_triage)
    logger.info("Tabela Gold 'tachycardia_triage.parquet' gerada com sucesso.")

    # 2. Tabela Gold: Decisão Cirúrgica vs. Sobrevivência
    query_surgical = f"""
    COPY (
        SELECT
            CASE
                WHEN ec.surgery = 1.0 THEN 'Com Cirurgia (Intervenção)'
                WHEN ec.surgery = 2.0 THEN 'Sem Cirurgia (Tratamento Clínico)'
                ELSE 'Não Informado'
            END AS surgery,
            COUNT(*) AS total_cases,
            ROUND(AVG(CASE WHEN ec.outcome_label = 'lived' THEN 100.0 ELSE 0.0 END), 1) AS survival_pct
        FROM read_parquet('{cases_path}') ec
        WHERE ec.surgery IN (1.0, 2.0) AND ec.outcome_label IS NOT NULL
        GROUP BY 1
    ) TO '{GOLD_DIR / "surgical_decision.parquet"}' (FORMAT PARQUET);
    """
    con.execute(query_surgical)
    logger.info("Tabela Gold 'surgical_decision.parquet' gerada com sucesso.")


if __name__ == "__main__":
    build_gold_tables()