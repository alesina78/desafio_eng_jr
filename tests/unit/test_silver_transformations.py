"""
Testes Unitários - Camada Silver e Transformações
------------------------------------------------
Objetivo:
    Validar as regras de limpeza, geração de chave primária ('case_id'),
    tipagem e integridade referencial utilizando pytest com DataFrames em memória,
    sem a necessidade de abrir um banco de dados real.
"""

import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def sample_raw_dataframe():
    """Retorna um DataFrame simulando dados brutos da camada Bronze."""
    data = {
        0: [1, 2, 1], # surgery
        1: [1, 1, 1], # age
        2: [530101, 530102, 530103], # hospital_number
        3: [38.5, "?", 38.3], # rectal_temperature
        4: [66, 88, 40], # pulse
        22: [1.0, 2.0, 3.0] # outcome (lived, died, euthanized)
    }
    df = pd.DataFrame(data)
    for col in range(len(df.columns), 28):
        df[col] = np.nan
    return df


def test_case_id_generation(sample_raw_dataframe):
    """Testa se o case_id é gerado corretamente começando em 1 e sem nulos."""
    df = sample_raw_dataframe.copy()
    df = df.reset_index()
    df = df.rename(columns={"index": "case_id"})
    df["case_id"] = df["case_id"] + 1
    
    assert "case_id" in df.columns
    assert df["case_id"].iloc[0] == 1
    assert df["case_id"].iloc[-1] == len(df)
    assert df["case_id"].isnull().sum() == 0


def test_outcome_mapping():
    """Testa se o mapeamento numérico do desfecho para labels textuais está correto."""
    mapping = {1.0: "lived", 2.0: "died", 3.0: "euthanized"}
    serie_outcomes = pd.Series([1.0, 2.0, 3.0, np.nan])
    serie_labels = serie_outcomes.map(mapping)
    
    assert serie_labels.iloc[0] == "lived"
    assert serie_labels.iloc[1] == "died"
    assert serie_labels.iloc[2] == "euthanized"
    assert pd.isna(serie_labels.iloc[3])


def test_relational_integrity_join():
    """Testa a integridade referencial entre equine_cases e clinical_measures via case_id."""
    cases = pd.DataFrame({
        "case_id": [1, 2],
        "hospital_number": [530101, 530102],
        "outcome_label": ["lived", "died"]
    })
    
    clinical = pd.DataFrame({
        "case_id": [1, 2],
        "pulse": [66, 88],
        "rectal_temperature": [38.5, 38.0]
    })
    
    merged = pd.merge(cases, clinical, on="case_id", how="inner")
    
    assert len(merged) == 2
    assert "pulse" in merged.columns
    assert "hospital_number" in merged.columns
    assert merged["case_id"].is_unique