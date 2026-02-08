/*
    Camada: Silver (Staging)
    Objetivo: Limpeza, tradução de colunas e tipagem forte.
    Origem: s3://data2eco-raw/gbif/apidae/
    Destino: s3://data2eco-silver/stg_gbif_apidae.parquet
*/
{{ config(
    location = 's3://data2eco-silver/stg_gbif_apidae.parquet'
) }}

WITH source AS (
    -- Lendo os arquivos brutos.
    -- O '*' garante que pegamos todas as colunas listadas no seu schema.

    SELECT
        *
    FROM
        read_parquet('s3://data2eco-raw/*/gbif_apidae_br.parquet')
),
renamed AS (
    SELECT
        "key" AS id_ocorrencia,
        basisOfRecord AS tipo_registro,
        scientificName AS nome_cientifico,
        decimalLatitude AS latitude,
        decimalLongitude AS longitude,
        stateProvince AS estado,
        municipality AS municipio,
        TRY_CAST(
            eventDate AS DATE
        ) AS data_evento,
        YEAR AS ano,
        MONTH AS mes,
        DAY AS dia
    FROM
        source
    WHERE
        basisOfRecord = 'HUMAN_OBSERVATION'
)
SELECT
    *
FROM
    renamed
