"""
Módulo de Ingestão de Dados - Camada Bronze
-------------------------------------------
Objetivo: 
    Baixar os arquivos brutos do dataset 'Horse Colic' diretamente do 
    Repositório UCI Machine Learning e salvá-los na camada Bronze 
    (/data/bronze) sem nenhuma alteração, garantindo a imutabilidade 
    do dado original.

Fonte dos Dados:
    - UCI Machine Learning Repository: Horse Colic Dataset
    - Licença: Creative Commons Attribution 4.0 International (CC BY 4.0)
"""

import os
import urllib.request
import logging

# Configuração básica de logs para rastreabilidade da execução
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# URLs oficiais dos arquivos brutos fornecidos pela UCI
URLS_UCI = {
    "horse-colic.data": "https://archive.ics.uci.edu/ml/machine-learning-databases/horse-colic/horse-colic.data",
    "horse-colic.test": "https://archive.ics.uci.edu/ml/machine-learning-databases/horse-colic/horse-colic.test"
}

# Caminho relativo para o diretório da Camada Bronze
CAMINHO_BRONZE = os.path.join("data", "bronze")


def criar_diretorio_bronze(diretorio: str) -> None:
    """
    Garante que o diretório de destino da camada Bronze exista.
    Se não existir, cria a estrutura de pastas automaticamente.
    """
    if not os.path.exists(diretorio):
        os.makedirs(diretorio, exist_ok=True)
        logger.info(f"Diretório criado com sucesso: {diretorio}")
    else:
        logger.info(f"Diretório já existente: {diretorio}")


def baixar_arquivos_brutos() -> None:
    """
    Itera sobre o dicionário de URLs e realiza o download de cada arquivo 
    bruto para a pasta da camada Bronze.
    """
    criar_diretorio_bronze(CAMINHO_BRONZE)
    
    logger.info("Iniciando processo de download da Camada Bronze...")

    for nome_arquivo, url in URLS_UCI.items():
        destino_completo = os.path.join(CAMINHO_BRONZE, nome_arquivo)
        
        logger.info(f"Baixando '{nome_arquivo}' a partir de: {url}")
        
        try:
            # Realiza o download do arquivo via HTTP e salva no destino
            urllib.request.urlretrieve(url, destino_completo)
            logger.info(f"Sucesso! Arquivo salvo em: {destino_completo}")
            
        except Exception as erro:
            logger.error(f"Falha crítica ao baixar o arquivo {nome_arquivo}. Erro: {erro}")
            raise

    logger.info("Processo de ingestão da Camada Bronze concluído com sucesso!")


if __name__ == "__main__":
    # Ponto de entrada principal do script de ingestão
    baixar_arquivos_brutos()