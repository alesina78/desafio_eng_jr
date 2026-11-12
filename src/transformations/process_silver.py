"""
Módulo de Transformação - Camada Silver
---------------------------------------
Objetivo:
    Ler os dados brutos da camada Bronze (Horse Colic .data e .test),
    realizar a limpeza, tratar valores ausentes ('?'), tipar as colunas,
    gerar a chave relacional 'case_id' e dividir o dataset normalizado 
    em duas tabelas limpas na camada Silver:
        1. equine_cases (dados cadastrais, lesões e desfechos)
        2. clinical_measures (sinais vitais e avaliações clínicas)
"""

import os
import pandas as pd
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Nomes oficiais das 28 colunas do dataset Horse Colic (UCI)
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


def carregar_dados_brutos() -> pd.DataFrame:
    """Lê os arquivos .data e .test da Bronze e os une em um único DataFrame."""
    caminho_data = os.path.join(DIR_BRONZE, "horse-colic.data")
    caminho_test = os.path.join(DIR_BRONZE, "horse-colic.test")
    
    logger.info("Carregando arquivos brutos da camada Bronze...")
    
    # O dataset usa espaços múltiplos como separador e '?' para nulos
    df_data = pd.read_csv(caminho_data, sep=r"\s+", engine="python", header=None, names=COLUNAS_HORSE_COLIC, na_values="?")
    df_test = pd.read_csv(caminho_test, sep=r"\s+", engine="python", header=None, names=COLUNAS_HORSE_COLIC, na_values="?")
    
    df_completo = pd.concat([df_data, df_test], ignore_index=True)
    logger.info(f"Total de registros brutos carregados: {df_completo.shape[0]}")
    
    return df_completo


def processar_camada_silver() -> None:
    """Executa a limpeza, estruturação e divisão das tabelas na camada Silver."""
    os.makedirs(DIR_SILVER, exist_ok=True)
    
    df = carregar_dados_brutos()
    
    logger.info("Iniciando limpeza e normalização na camada Silver...")
    
    # 1. Gerar uma chave primária única (case_id) para cada atendimento
    df = df.reset_index()
    df = df.rename(columns={"index": "case_id"})
    df["case_id"] = df["case_id"] + 1  # Começar em 1
    
    # 2. Filtrar apenas os registros que possuem um desfecho válido (removendo nulos no outcome)
    df = df.dropna(subset=["outcome"])
    
    # Mapear códigos de desfecho para termos legíveis (opcional, mas excelente para análise)
    # 1 = lived, 2 = died, 3 = euthanized
    mapa_desfecho = {1.0: "lived", 2.0: "died", 3.0: "euthanized"}
    df["outcome_label"] = df["outcome"].map(mapa_desfecho)

    # 3. Criar a Tabela 1: equine_cases (Atendimento e Desfecho)
    df_cases = df[[
        "case_id", 
        "hospital_number", 
        "age", 
        "surgery", 
        "surgical_lesion", 
        "outcome", 
        "outcome_label"
    ]].copy()
    
    # 4. Criar a Tabela 2: clinical_measures (Sinais Vitais e Exames)
    df_clinical = df[[
        "case_id", "rectal_temperature", "pulse", "respiratory_rate",
        "temp_of_extremities", "mucous_membranes", "capillary_refill_time",
        "pain", "peristalsis", "abdominal_distension", "packed_cell_volume", "total_protein"
    ]].copy()
    
    # Salvar as tabelas tratadas na pasta Silver (formato Parquet — consumido pela Gold)
    caminho_cases = os.path.join(DIR_SILVER, "equine_cases.parquet")
    caminho_clinical = os.path.join(DIR_SILVER, "clinical_measures.parquet")

    df_cases.to_parquet(caminho_cases, index=False)
    df_clinical.to_parquet(caminho_clinical, index=False)

    logger.info(f"Tabela salva com sucesso: {caminho_cases} ({df_cases.shape[0]} linhas)")
    logger.info(f"Tabela salva com sucesso: {caminho_clinical} ({df_clinical.shape[0]} linhas)")
    logger.info("Processamento da Camada Silver concluído com sucesso!")


if __name__ == "__main__":
    processar_camada_silver()