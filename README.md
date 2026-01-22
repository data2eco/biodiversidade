# Monitoramento de biodiversidade de polinizadores na cafeicultura

## Visão geral
Este projeto foi desenvolvido pela consultoria **Data2Eco** para atender uma grande cooperativa de produtores de café no Brasil. O objetivo é investigar a hipótese de que a diminuição da produtividade nas lavouras nos últimos 20 anos está correlacionada ao declínio de polinizadores naturais (especificamente abelhas nativas da família *Apidae*).

Como não é possível medir diretamente a "ausência" de abelhas em dados históricos, utilizamos dados de ocorrência do GBIF como base para criar um proxy de **variação da riqueza de espécies observada**.

## O problema de negócio
A polinização natural é um serviço ecossistêmico crucial para a qualidade e quantidade do café produzido. A cooperativa identificou uma tendência de queda de produtividade que não se explica apenas por fatores climáticos ou de solo. A suspeita recai sobre a perda de biodiversidade local.

Precisamos responder: **A diversidade de espécies de abelhas observadas nas regiões cafeeiras diminuiu entre as décadas de 2000-2010 e 2011-2023?**

## Metodologia e métrica (proxy)
Utilizamos a API do [GBIF](https://www.gbif.org/) (Global Biodiversity Information Facility) para extrair registros de ocorrência.

A métrica principal é a **Variação da Riqueza de Espécies por Década**.
* **Definição:** Contagem distinta de `scientific_name` observados em uma região (estado) dentro de um bloco temporal.
* **Lógica:** Se em Minas Gerais observamos 50 espécies distintas entre 2000-2010, e apenas 30 espécies distintas entre 2011-2023 (com esforço de amostragem similar), temos um indicativo de perda de biodiversidade.

## Arquitetura técnica
O projeto segue uma arquitetura moderna de dados (ELT):

1.  **Ingestão (Extract):** Scripts Python que consomem a API de busca do GBIF com paginação e salvam os dados brutos.
2.  **Armazenamento (Load):** Dados carregados em Data Warehouse (DuckDB/Postgres).
3.  **Transformação (Transform):** Uso de **dbt** (data build tool) seguindo a arquitetura medalhão:
    * **Bronze:** Dados brutos tipados.
    * **Silver:** Limpeza de coordenadas nulas, filtros taxonômicos e deduplicação.
    * **Gold:** Agregações por década e cálculo das variações percentuais.

## Como reproduzir

### 1. Preparação do Ambiente
Garanta que você tem o Python instalado. Clone o repositório, ative seu ambiente virtual e instale as dependências:
```bash
pip install -r requirements.txt
```

### 2. Execução da Ingestão (Extract)
O script de ingestão (`scripts/extract_gbif.py`) suporta diferentes modos de operação:

* **Modo Automático (Padrão):**
  Baixa todo o histórico definido no escopo (2000 a 2023) e salva apenas em Parquet.
  ```bash
  python scripts/extract_gbif.py
  ```

* **Modo Personalizado (Anos Específicos):**
  Baixa apenas os anos solicitados via argumento.
  ```bash
  python scripts/extract_gbif.py --years 2022 2023
  ```

* **Modo Visual (Gerar Excel):**
  Adicione a flag `--excel` para gerar também arquivos `.xlsx` para conferência manual (útil para stakeholders não-técnicos).
  ```bash
  python scripts/extract_gbif.py --years 2023 --excel
  ```

### 3. Transformação (Transform)
*Etapa em configuração.*
1. Configure seu `profiles.yml` do dbt.
2. Execute as transformações e testes:
   ```bash
   dbt run
   ```

---
**Status do projeto:** Ingestão concluída. Iniciando modelagem de dados.