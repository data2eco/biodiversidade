# Monitoramento de biodiversidade de polinizadores (data2eco)

## Visão geral
Este projeto foi desenvolvido pela consultoria data2eco para atender uma grande cooperativa de produtores de café no Brasil. O objetivo é investigar a hipótese de que a diminuição da produtividade nas lavouras nos últimos 20 anos está correlacionada ao declínio de polinizadores naturais (especificamente abelhas nativas da família apidae).

Como não é possível medir diretamente a "ausência" de abelhas em dados históricos, utilizamos dados de ocorrência do gbif como base para criar um proxy de variação da riqueza de espécies observada.

## O problema de negócio
A polinização natural é um serviço ecossistêmico crucial para a qualidade e quantidade do café produzido. A cooperativa identificou uma tendência de queda de produtividade que não se explica apenas por fatores climáticos ou de solo. A suspeita recai sobre a perda de biodiversidade local.

Precisamos responder: a diversidade de espécies de abelhas observadas nas regiões cafeeiras diminuiu entre as décadas de 2000-2010 e 2011-2023?

## Metodologia e métrica (proxy)
Utilizamos a api do gbif (global biodiversity information facility) para extrair registros de ocorrência.

A métrica principal é a variação da riqueza de espécies por década.
* Definição: contagem distinta de scientific_name observados em uma região (estado) dentro de um bloco temporal.
* Lógica: se em Minas Gerais observamos 50 espécies distintas entre 2000-2010, e apenas 30 espécies distintas entre 2011-2023 (com esforço de amostragem similar), temos um indicativo de perda de biodiversidade.

## Arquitetura técnica

![arquitetura](assets/arquitetura.png)

O projeto segue uma arquitetura moderna de dados (elt) conteinerizada:

1. Infraestrutura: docker orquestrando postgresql (warehouse) e localstack (simulador aws s3).
2. Ingestão (extract): scripts python consomem a api do gbif e depositam arquivos parquet brutos no data lake (s3 local).
3. Armazenamento (load): ingestão dos dados do s3 para tabelas raw no postgresql.
4. Transformação (transform): uso de dbt (data build tool) seguindo a arquitetura medalhão:
    * Bronze: dados brutos tipados e padronizados.
    * Silver: limpeza de coordenadas, filtros taxonômicos e deduplicação.
    * Gold: agregações analíticas e cálculo das variações percentuais.

## Como reproduzir

### 1. Preparação da infraestrutura (docker)
Este projeto utiliza docker para garantir reprodutibilidade.

1. Crie um arquivo .env na raiz com as credenciais (veja docker-compose.yml para os valores padrão).
2. Inicie os serviços:
```bash
docker-compose up -d
```
Isso iniciará o banco de dados e criará automaticamente o bucket s3 data2eco-raw.

### 2. Configuração do ambiente python
Recomendamos o uso de um ambiente virtual (venv ou uv).

```bash
# Instalar dependências
pip install -r requirements.txt
```

### 3. Execução da ingestão (extract)
O script de ingestão (scripts/extract_gbif.py) suporta diferentes modos:

* Modo padrão (full history): baixa todo o histórico (2000-2023) e salva no data lake s3.
* Modo personalizado (anos específicos):
  ```bash
  python scripts/extract_gbif.py --years 2022 2023
  ```
* Modo debug (gerar excel local): gera cópia local em .xlsx para conferência rápida.

### 4. Transformação (dbt)
Etapa em desenvolvimento.
1. Configure o profiles.yml para conectar ao postgres na porta 5432.
2. Execute as transformações:
   ```bash
   dbt run
   ```

---
**Status do projeto:** infraestrutura configurada. ingestão em adaptação para s3.