import io
import os

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from scripts.logger import setup_logger

# Configuração do Logger
logger = setup_logger(__name__)

# Configurações padrão
DEFAULT_ENDPOINT_URL = "http://localhost:4566"
DEFAULT_REGION = "us-east-1"
BUCKET_NAME = "data2eco-raw"


def get_s3_client():
    """
    Retorna um cliente S3 configurado.
    Prioriza variáveis de ambiente, mas usa padrões para LocalStack se não estiverem definidas.
    """
    endpoint_url = os.getenv("ENDPOINT_URL", DEFAULT_ENDPOINT_URL)

    # Para LocalStack, credenciais dummy são frequentemente necessárias se não configuradas no ambiente
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "test")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "test")
    region_name = os.getenv("AWS_DEFAULT_REGION", DEFAULT_REGION)

    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name,
    )


def upload_dataframe_to_s3(df, file_name, bucket_name=BUCKET_NAME):
    """
    Converte um DataFrame para Parquet em memória e faz upload para o S3.
    """
    s3_client = get_s3_client()

    try:
        # Buffer em memória para o arquivo Parquet
        parquet_buffer = io.BytesIO()
        df.to_parquet(parquet_buffer, index=False)
        parquet_buffer.seek(0)

        logger.info(f"Iniciando upload de {file_name} para o bucket {bucket_name}...")

        s3_client.upload_fileobj(parquet_buffer, bucket_name, file_name)

        logger.info(
            f"Sucesso! Arquivo {file_name} enviado para s3://{bucket_name}/{file_name}"
        )
        return True

    except NoCredentialsError:
        logger.error("Credenciais da AWS não encontradas.")
        return False
    except ClientError as e:
        logger.error(f"Falha no upload para o S3: {e}")
        return False
    except Exception as e:
        logger.error(f"Erro inesperado ao salvar no S3: {e}")
        return False
