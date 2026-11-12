"""
Pipeline de Validação Contratual — Camada Silver (Horse Colic Observatory)
===========================================================================

Este módulo orquestra a execução dos contratos de dados (`pandera`) sobre os
DataFrames transformados da camada Bronze para a Silver em uma única passagem
(single-pass validation).

Fluxo de Saída (Outputs):
    1. **Aprovados (Silver)**: Registros em conformidade com o schema clínico são
       persistidos em formato colunar otimizado (`.parquet`).
    2. **Reprovados (Quarentena)**: Registros violadores são isolados em
       `data/silver/quarantine/` enriquecidos com colunas de auditoria
       (`_rejection_reason` e `_rejected_at`).
    3. **Observabilidade (Relatório)**: Métricas de volumetria, taxa de aprovação,
       completude (nulos) e distribuição de falhas são salvas em formato `.json`.

Autor: Engenharia de Dados / Horse Colic Observatory
Versão do Contrato: 1.0.0
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Final

import pandas as pd
from pandera.errors import SchemaErrors

from src.silver.schemas import CLINICAL_SCHEMA, EQUINE_SCHEMA

# ==============================================================================
# CONFIGURAÇÕES DE DIRETÓRIOS E IDENTIFICADOR DE EXECUÇÃO
# ==============================================================================
SCHEMA_VERSION: Final[str] = "v1.0.0"

SILVER_DIR: Final[Path] = Path("data/silver")
QUARANTINE_DIR: Final[Path] = SILVER_DIR / "quarantine"
REPORTS_DIR: Final[Path] = SILVER_DIR / "quality_reports"

# Garante que a estrutura de pastas exista antes da execução do pipeline
QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Timestamp único da execução utilizado para rastreabilidade e versionamento de logs
RUN_DATE: Final[str] = datetime.now().strftime("%Y%m%d_%H%M%S")

# Configuração básica de logger para monitoramento em tempo de execução
logger = logging.getLogger(__name__)


# ==============================================================================
# NÚCLEO DE VALIDAÇÃO E PARTICIONAMENTO (APPROVED vs. QUARANTINE)
# ==============================================================================

def validate_and_split(
    df_cases: pd.DataFrame,
    df_clinical: pd.DataFrame,
) -> dict[str, Any]:
    """
    Valida os DataFrames de casos e medidas clínicas contra os schemas Pandera
    e separa registros aprovados dos reprovados sem interromper o pipeline.

    Utiliza `lazy=True` para avaliar todas as linhas e regras antes de lançar
    `SchemaErrors`, permitindo mapear todas as falhas de cada registro de uma só vez.

    Args:
        df_cases (pd.DataFrame): DataFrame com dados cadastrais e desfecho dos equinos.
        df_clinical (pd.DataFrame): DataFrame com sinais vitais e exames laboratoriais.

    Returns:
        dict[str, Any]: Dicionário estruturado contendo:
            - `approved_cases` (pd.DataFrame): Casos válidos.
            - `rejected_cases` (pd.DataFrame): Casos inválidos com motivo de rejeição.
            - `approved_clinical` (pd.DataFrame): Medidas clínicas válidas.
            - `rejected_clinical` (pd.DataFrame): Medidas clínicas inválidas com motivo.
            - `quality_report` (dict): Dicionário consolidado de métricas de qualidade.
    """
    results: dict[str, Any] = {}

    validation_targets = [
        ("cases", df_cases, EQUINE_SCHEMA),
        ("clinical", df_clinical, CLINICAL_SCHEMA),
    ]

    for label, df, schema in validation_targets:
        try:
            # Executa validação preguiçosa (coleta todos os erros antes de falhar)
            validated_df = schema.validate(df, lazy=True)
            results[f"approved_{label}"] = validated_df
            results[f"rejected_{label}"] = pd.DataFrame()

        except SchemaErrors as err:
            # Extrai o DataFrame de diagnósticos gerado pelo Pandera
            failure_df: pd.DataFrame = err.failure_cases.copy()

            # Identifica os índices originais das linhas que falharam em pelo menos 1 regra
            bad_idx = failure_df["index"].dropna().unique()
            rejected = df.loc[df.index.isin(bad_idx)].copy()

            # Agrupa múltiplas falhas de uma mesma linha separando-as por pipe (" | ")
            reason_map: dict[Any, str] = (
                failure_df.groupby("index")["check"]
                .apply(lambda checks: " | ".join(checks.astype(str).unique()))
                .to_dict()
            )

            # Enriquece os registros de quarentena com metadados de auditoria
            rejected["_rejection_reason"] = rejected.index.map(reason_map)
            rejected["_rejected_at"] = RUN_DATE

            # Separa registros limpos dos registros enviados para quarentena
            results[f"approved_{label}"] = df.loc[~df.index.isin(bad_idx)].copy()
            results[f"rejected_{label}"] = rejected

    # Gera o relatório de observabilidade consolidando as duas tabelas
    results["quality_report"] = _build_report(df_cases, df_clinical, results)
    return results


# ==============================================================================
# CONSTRUÇÃO DO RELATÓRIO DE QUALIDADE DE DADOS (DATA QUALITY REPORT)
# ==============================================================================

def _build_report(
    raw_cases: pd.DataFrame,
    raw_clinical: pd.DataFrame,
    results: dict[str, Any],
) -> dict[str, Any]:
    """
    Constrói o payload estruturado do relatório de qualidade da execução.

    Calcula métricas de volumetria, taxa de aprovação, percentual de valores nulos
    por coluna na entrada e contagem agrupada por motivo de rejeição.

    Args:
        raw_cases (pd.DataFrame): DataFrame original de casos antes da validação.
        raw_clinical (pd.DataFrame): DataFrame original de medidas antes da validação.
        results (dict[str, Any]): Resultado retornado por `validate_and_split`.

    Returns:
        dict[str, Any]: Estrutura pronta para serialização em JSON.
    """

    def _compute_table_metrics(
        raw: pd.DataFrame,
        rejected: pd.DataFrame,
        table_name: str,
    ) -> dict[str, Any]:
        """Calcula indicadores estatísticos de qualidade para uma tabela individual."""
        total_input = len(raw)
        n_rejected = len(rejected) if not rejected.empty else 0
        n_approved = total_input - n_rejected
        approval_rate = round((n_approved / total_input) * 100, 2) if total_input > 0 else 0.0

        rejection_breakdown = (
            rejected["_rejection_reason"].value_counts().to_dict()
            if not rejected.empty
            else {}
        )

        return {
            "table": table_name,
            "total_input": total_input,
            "approved": n_approved,
            "rejected": n_rejected,
            "approval_rate_pct": approval_rate,
            "null_pct_per_column": raw.isnull().mean().mul(100).round(2).to_dict(),
            "rejection_reasons": rejection_breakdown,
        }

    return {
        "run_id": RUN_DATE,
        "schema_version": SCHEMA_VERSION,
        "tables": [
            _compute_table_metrics(raw_cases, results["rejected_cases"], "equine_cases"),
            _compute_table_metrics(raw_clinical, results["rejected_clinical"], "clinical_measures"),
        ],
    }


# ==============================================================================
# ORQUESTRADOR DE PERSISTÊNCIA (ENTRY POINT DO PIPELINE)
# ==============================================================================

def run_validation(
    df_cases: pd.DataFrame,
    df_clinical: pd.DataFrame,
) -> dict[str, Any]:
    """
    Executa o fluxo completo de validação contratual e persiste os artefatos em disco.

    Artefatos gerados:
        - `data/silver/equine_cases.parquet` (sobrescrito com a versão limpa mais recente)
        - `data/silver/clinical_measures.parquet` (sobrescrito com a versão limpa mais recente)
        - `data/silver/quarantine/rejected_<tabela>_<RUN_DATE>.parquet` (se houver falhas)
        - `data/silver/quality_reports/quality_report_<RUN_DATE>.json`

    Args:
        df_cases (pd.DataFrame): DataFrame de casos vindo da transformação Bronze -> Silver.
        df_clinical (pd.DataFrame): DataFrame clínico vindo da transformação Bronze -> Silver.

    Returns:
        dict[str, Any]: Dicionário contendo os DataFrames processados e o relatório gerado.
    """
    results = validate_and_split(df_cases, df_clinical)

    # 1. Persistência dos dados aprovados na camada Silver
    results["approved_cases"].to_parquet(SILVER_DIR / "equine_cases.parquet", index=False)
    results["approved_clinical"].to_parquet(SILVER_DIR / "clinical_measures.parquet", index=False)

    # 2. Persistência condicional dos registros reprovados na Quarentena
    for label in ("cases", "clinical"):
        rejected_df: pd.DataFrame = results[f"rejected_{label}"]
        if not rejected_df.empty:
            quarantine_path = QUARANTINE_DIR / f"rejected_{label}_{RUN_DATE}.parquet"
            rejected_df.to_parquet(quarantine_path, index=False)
            logger.warning(
                "[QUARANTINE] %d registros rejeitados de '%s' -> %s",
                len(rejected_df),
                label,
                quarantine_path,
            )

    # 3. Persistência do relatório de qualidade em JSON (UTF-8 para preservar acentuação)
    report_path = REPORTS_DIR / f"quality_report_{RUN_DATE}.json"
    with open(report_path, "w", encoding="utf-8") as file:
        json.dump(results["quality_report"], file, indent=2, ensure_ascii=False)

    logger.info("[QUALITY REPORT] Relatório salvo com sucesso -> %s", report_path)
    return results
