#!/bin/bash
echo "Iniciando configuração do LocalStack S3..."

# Cria o bucket 'data2eco-raw-data'
awslocal s3 mb s3://data2eco-raw-data

echo "Bucket 'data2eco-raw-data' criado com sucesso!"