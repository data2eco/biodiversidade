import time

import pandas as pd
import requests

import scripts.s3_manager as s3_manager
from scripts.logger import setup_logger

# Configuração do Logger
logger = setup_logger(__name__)

# --- Configurações Globais ---
# Família Apidae (abelhas) = 4334
# País Brasil = BR
BASE_URL = "https://api.gbif.org/v1/occurrence/search"
TAXON_KEY = 4334
COUNTRY = "BR"
PAGE_SIZE = 300  # Limite máximo seguro por página síncrona
START_YEAR = 2000
END_YEAR = 2023


def construct_default_params(offset: int, year: int) -> dict:
    """
    Constrói o dicionário de parâmetros para a consulta na API do GBIF.

    Args:
        offset (int): O índice de deslocamento (offset) para paginação.
        year (int): O ano de filtro para a busca.

    Returns:
        dict: Um dicionário contendo os parâmetros configurados (familyKey, country, limit, etc).
    """
    return {
        "familyKey": TAXON_KEY,
        "country": COUNTRY,
        "year": year,
        "limit": PAGE_SIZE,
        "offset": offset,
        "hasCoordinate": "true",  # Apenas dados com lat/long
        "hasGeospatialIssue": "false",
    }


def fetch_gbif_data(params: dict, base_url: str = BASE_URL) -> dict:
    """
    Executa a requisição HTTP GET contra a API do GBIF.

    Args:
        params (dict): Dicionário de parâmetros de consulta (query string).
        base_url (str, optional): URL base da API. Defaults to BASE_URL.

    Returns:
        dict: O JSON de resposta da API convertido para dicionário Python.

    Raises:
        requests.exceptions.RequestException: Se houver erro na requisição HTTP.
    """
    response = requests.get(base_url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_data_by_year(year: int) -> list:
    """
    Busca todos os registros de ocorrência para um ano específico,
    lidando automaticamente com a paginação da API.

    Args:
        year (int): O ano para o qual os dados serão buscados.

    Returns:
        list: Uma lista de dicionários, onde cada dicionário é um registro de ocorrência.
    """
    end_of_records = False
    all_records = []

    logger.info(f"Iniciando extração para o ano {year}")

    while not end_of_records:
        # O offset é baseado na quantidade de registros já coletados
        offset = len(all_records)
        params = construct_default_params(offset, year)

        try:
            data = fetch_gbif_data(params)
            results = data.get("results", [])
            all_records.extend(results)

            # Controle de paginação fornecido pela API
            end_of_records = data.get("endOfRecords")
            count = len(results)

            # Se a lista de resultados vier vazia, forçamos o fim da iteração
            if count == 0:
                end_of_records = True

            # Log de progresso (substituto visual dos pontos)
            logger.info(
                f"Ano {year}: Baixados +{count} registros (Total parcial: {len(all_records)})"
            )

            # Pausa para evitar rate limiting da API
            time.sleep(0.3)

        except Exception as e:
            logger.error(
                f"Falha na requisição para o ano {year} (offset {offset}): {e}"
            )
            break

    logger.info(f"Concluído ano {year}: {len(all_records)} registros baixados.")
    return all_records


def save_data(records: list, year: int) -> None:
    """
    Processa e salva os registros brutos no Data Lake (S3) em formato Parquet.

    A função seleciona colunas específicas de interesse e converte tipos básicos
    antes de enviar para o S3 via módulo s3_manager.

    Args:
        records (list): Lista de registros (dicionários) retornados pela API.
        year (int): Ano correspondente aos dados, usado para nomear o arquivo.
    """
    if not records:
        logger.warning(f"Nenhum dado encontrado para {year}.")
        return

    df = pd.DataFrame(records)

    # Selecionando colunas de interesse para reduzir tamanho e complexidade
    cols_interest = [
        "key",
        "scientificName",
        "decimalLatitude",
        "decimalLongitude",
        "eventDate",
        "year",
        "month",
        "day",
        "stateProvince",
        "municipality",
        "basisOfRecord",
    ]

    # Garante que só pegamos colunas que realmente existem no DataFrame
    existing_cols = [c for c in cols_interest if c in df.columns]
    df = df[existing_cols]

    # Garante tipo numérico para o ano para consistência
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce")

    # Define o caminho no S3 (particionamento lógico por nome de arquivo/pasta)
    file_name = f"{year}/gbif_apidae_br.parquet"

    logger.info(f"Enviando {len(df)} registros para S3: {file_name}")
    s3_manager.upload_dataframe_to_s3(df, file_name)


if __name__ == "__main__":
    logger.info(f"Iniciando carga de dados de {START_YEAR} a {END_YEAR}...")

    for year in range(START_YEAR, END_YEAR + 1):
        records = fetch_data_by_year(year)
        save_data(records, year)

    logger.info("Carga completa finalizada")
