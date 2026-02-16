#!/bin/bash

# --- CONFIGURAÇÃO ---
BUCKET_RAW="data2eco-raw"
BUCKET_SILVER="data2eco-silver"
BUCKET_GOLD="data2eco-gold"

# Caminho do dbt (relativo à raiz onde o script é rodado)
DBT_DIR="dbt_project"

# Definições para o LocalStack
ENDPOINT_URL="http://localhost:4566"
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
export AWS_PAGER="" # Desativa o editor de texto do CLI

# Cores para o terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== INICIANDO AMBIENTE DE DESENVOLVIMENTO ===${NC}"

# ------------------------------------------------------------------
# 1. GARANTIR O DOCKER COMPOSE (INFRAESTRUTURA)
# ------------------------------------------------------------------
if [ ! -f "docker-compose.yml" ]; then
    echo "docker-compose.yml não encontrado. Criando arquivo com persistência..."
    cat <<EOF > docker-compose.yml
services:
  localstack:
    container_name: localstack-main
    image: localstack/localstack
    ports:
      - "127.0.0.1:4566:4566"
    environment:
      - PERSISTENCE=1
      - DEBUG=0
    volumes:
      - "./volume:/var/lib/localstack"
      - "/var/run/docker.sock:/var/run/docker.sock"
EOF
    echo -e "${GREEN}✔ docker-compose.yml criado.${NC}"
fi

# ------------------------------------------------------------------
# 2. SUBIR O LOCALSTACK
# ------------------------------------------------------------------
echo "Subindo containers Docker..."
docker compose up -d

echo "Aguardando LocalStack responder (pode levar alguns segundos)..."

# Loop de verificação de saúde do serviço
until aws --endpoint-url=$ENDPOINT_URL s3 ls > /dev/null 2>&1; do
  printf '.'
  sleep 2
done
echo ""
echo -e "${GREEN}✔ LocalStack está online!${NC}"

# ------------------------------------------------------------------
# 3. CRIAR BUCKETS (DATA LAKE)
# ------------------------------------------------------------------
echo -e "${BLUE}--- Verificando Buckets S3 ---${NC}"

create_bucket() {
    local bucket_name=$1
    if aws --endpoint-url=$ENDPOINT_URL s3api head-bucket --bucket "$bucket_name" > /dev/null 2>&1; then
        echo "  - Bucket '$bucket_name' já existe."
    else
        aws --endpoint-url=$ENDPOINT_URL s3 mb "s3://$bucket_name" > /dev/null
        echo -e "${GREEN}  + Bucket '$bucket_name' criado.${NC}"
    fi
}

create_bucket $BUCKET_RAW
create_bucket $BUCKET_SILVER
create_bucket $BUCKET_GOLD

# ------------------------------------------------------------------
# 4. EXECUTAR O DBT (TRANSFORMAÇÃO)
# ------------------------------------------------------------------


if [ -d "$DBT_DIR" ]; then
    echo -e "${BLUE}--- Iniciando dbt ---${NC}"
    cd "$DBT_DIR"

    # Verifica se as dependências já foram instaladas
    if [ ! -d "dbt_packages" ]; then
        echo "Instalando dependências do dbt..."
        uv run dbt deps
    fi

    # Testa a conexão (Debug)
    echo "Verificando conexão do dbt..."
    if uv run dbt debug > /dev/null 2>&1; then
        echo -e "${GREEN}✔ Conexão dbt OK.${NC}"
    else
        echo -e "\033[0;31m✘ Erro na conexão do dbt. Verifique o profiles.yml\033[0m"
        # Não sai do script, tenta rodar mesmo assim para mostrar o erro real
    fi

    echo "Rodando modelos dbt..."
    uv run dbt run

    cd ..
else
    echo -e "\033[0;31mERRO: Pasta '$DBT_DIR' não encontrada.\033[0m"
fi
