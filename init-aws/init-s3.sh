#!/bin/bash

# Inicia o LocalStack em background
echo "Iniciando LocalStack..."
localstack start -d

# Aguarda até que os serviços estejam prontos
echo "Aguardando LocalStack ficar pronto..."
localstack wait -t 30

BUCKET_NAME="data2eco-raw-data"

# Configuração do Endpoint: Aponta para o LocalStack.
# PARA MIGRAR PARA AWS REAL: Basta comentar ou deixar vazia a variável ENDPOINT_URL abaixo
ENDPOINT_URL="http://localhost:4566"

# Configura as opções do comando AWS baseadas na presença do ENDPOINT_URL
if [ -n "$ENDPOINT_URL" ]; then
    AWS_OPTS="--endpoint-url $ENDPOINT_URL"
    
    # Credenciais dummy necessárias para o LocalStack (ignorar para AWS Real)
    export AWS_ACCESS_KEY_ID=test
    export AWS_SECRET_ACCESS_KEY=test
    export AWS_DEFAULT_REGION=us-east-1
else
    AWS_OPTS=""
fi

echo "Verificando existência do bucket '$BUCKET_NAME'..."

# Verifica se o bucket existe (head-bucket retorna 0 se existe, erro se não)
if aws s3api head-bucket --bucket "$BUCKET_NAME" $AWS_OPTS 2>/dev/null; then
    echo "Bucket '$BUCKET_NAME' já existe."
else
    echo "Bucket não encontrado. Criando bucket '$BUCKET_NAME'..."
    aws s3 mb "s3://$BUCKET_NAME" $AWS_OPTS
    echo "Bucket '$BUCKET_NAME' criado com sucesso!"
fi
