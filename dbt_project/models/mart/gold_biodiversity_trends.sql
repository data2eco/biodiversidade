/*
    Camada: Gold (Mart)
    Objetivo: Métricas de riqueza de espécies de abelhas por estado e período.
    Origem: stg_gbif_apidae (Camada Silver)
    Destino: s3://data2eco-gold/gold_biodiversity_trends.parquet

    Métricas:
    - riqueza_2000_2010: COUNT(DISTINCT nome_cientifico) no período 2000-2010
    - riqueza_2011_2023: COUNT(DISTINCT nome_cientifico) no período 2011-2023
    - variacao_percentual: Variação % entre os dois períodos por estado
*/
{{ config(
    location = 's3://data2eco-gold/gold_biodiversity_trends.parquet'
) }}

WITH ocorrencias AS (
    SELECT
        nome_cientifico,
        estado,
        ano,
        CASE
            WHEN ano BETWEEN 2000 AND 2010 THEN '2000-2010'
            WHEN ano BETWEEN 2011 AND 2023 THEN '2011-2023'
        END AS periodo
    FROM {{ ref('stg_gbif_apidae') }}
    WHERE
        estado IS NOT NULL
        AND nome_cientifico IS NOT NULL
        AND ano BETWEEN 2000 AND 2023
),

riqueza_por_periodo AS (
    SELECT
        estado,
        periodo,
        COUNT(DISTINCT nome_cientifico) AS riqueza_especies
    FROM ocorrencias
    WHERE periodo IS NOT NULL
    GROUP BY estado, periodo
),

pivotado AS (
    SELECT
        estado,
        MAX(CASE WHEN periodo = '2000-2010' THEN riqueza_especies END) AS riqueza_2000_2010,
        MAX(CASE WHEN periodo = '2011-2023' THEN riqueza_especies END) AS riqueza_2011_2023
    FROM riqueza_por_periodo
    GROUP BY estado
)

SELECT
    estado,
    COALESCE(riqueza_2000_2010, 0) AS riqueza_2000_2010,
    COALESCE(riqueza_2011_2023, 0) AS riqueza_2011_2023,
    ROUND(
        (riqueza_2011_2023 - riqueza_2000_2010) * 100.0
        / NULLIF(riqueza_2000_2010, 0),
        2
    ) AS variacao_percentual
FROM pivotado
ORDER BY variacao_percentual ASC
