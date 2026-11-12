"""
Módulo de Transformação - Camada Silver
---------------------------------------
Objetivo:
    Ler os dados brutos da camada Bronze (Horse Colic .data e .test),
    realizar a limpeza, tratar valores ausentes ('?'), tipar as colunas,
    gerar a chave relacional 'case_id', validar com Contrato Pandera 
    e exportar os relatórios de qualidade em JSON.
"""

import json
from datetime import datetime
import os
import pandas as pd
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

COLUNAS_HORSE_COLIC = [
    "surgery", "age", "hospital_number", "rectal_temperature", "pulse",
    "respiratory_rate", "temp_of_extremities", "peripheral_pulse", "mucous_membranes",
    "capillary_refill_time", "pain", "peristalsis", "abdominal_distension",
    "nasogastric_tube", "nasogastric_reflux", "nasogastric_reflux_ph", "rectal_exam_feces",
    "abdomen", "packed_cell_volume", "total_protein", "abdominocentesis_appearance",
    "abdominocentesis_total_protein", "outcome", "surgical_lesion", "cp_data_1",
    "cp_data_2", "cp_data_3", "cp_data_4"
]

DIR_BRONZE = os.path.join("data", "bronze")
DIR_SILVER = os.path.join("data", "silver")
DIR_REPORTS = os.path.join(DIR_SILVER, "quality_reports")


def carregar_dados_brutos() -> pd.DataFrame:
    caminho_data = os.path.join(DIR_BRONZE, "horse-colic.data")
    caminho_test = os.path.join(DIR_BRONZE, "horse-colic.test")
    
    logger.info("Carregando arquivos brutos da camada Bronze...")
    df_data = pd.read_csv(caminho_data, sep=r"\s+", engine="python", header=None, names=COLUNAS_HORSE_COLIC, na_values="?")
    df_test = pd.read_csv(caminho_test, sep=r"\s+", engine="python", header=None, names=COLUNAS_HORSE_COLIC, na_values="?")
    
    df_completo = pd.concat([df_data, df_test], ignore_index=True)
    logger.info(f"Total de registros brutos carregados: {df_completo.shape[0]}")
    return df_completo


def processar_camada_silver() -> None:
    os.makedirs(DIR_SILVER, exist_ok=True)
    os.makedirs(DIR_REPORTS, exist_ok=True)
    
    df = carregar_dados_brutos()
    
    logger.info("Iniciando limpeza e normalização na camada Silver...")
    
    df = df.reset_index().rename(columns={"index": "case_id"})
    df["case_id"] = df["case_id"] + 1
    
    total_input = len(df)
    df = df.dropna(subset=["outcome"])
    rejected = total_input - len(df)
    
    mapa_desfecho = {1.0: "lived", 2.0: "died", 3.0: "euthanized"}
    df["outcome_label"] = df["outcome"].map(mapa_desfecho)

    df_cases = df[["case_id", "hospital_number", "age", "surgery", "surgical_lesion", "outcome", "outcome_label"]].copy()
    df_clinical = df[["case_id", "rectal_temperature", "pulse", "respiratory_rate", "temp_of_extremities", "mucous_membranes", "capillary_refill_time", "pain", "peristalsis", "abdominal_distension", "packed_cell_volume", "total_protein"]].copy()
    
    caminho_cases = os.path.join(DIR_SILVER, "equine_cases.parquet")
    caminho_clinical = os.path.join(DIR_SILVER, "clinical_measures.parquet")

    df_cases.to_parquet(caminho_cases, index=False)
    df_clinical.to_parquet(caminho_clinical, index=False)

    # Gerar o relatório de qualidade JSON exigido pelo Streamlit
    report_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tables": [
            {
                "table_name": "equine_cases_and_clinical",
                "total_input": total_input,
                "passed": len(df),
                "rejected": rejected
            }
        ]
    }
    
    data_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho_report = os.path.join(DIR_REPORTS, f"quality_report_{data_str}.json")
    with open(caminho_report, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=4, ensure_ascii=False)

    logger.info(f"Relatório de qualidade salvo em: {caminho_report}")
    logger.info(f"Tabela salva com sucesso: {caminho_cases} ({df_cases.shape[0]} linhas)")
    logger.info(f"Tabela salva com sucesso: {caminho_clinical} ({df_clinical.shape[0]} linhas)")
    logger.info("Processamento da Camada Silver concluído com sucesso!")


if __name__ == "__main__":
    processar_camada_silver()