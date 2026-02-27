"""
Visualização: Riqueza de Espécies de Abelhas (Apidae) no Brasil
Camada: Gold (Mart) — gold_biodiversity_trends

Execução:
    streamlit run app/visualizacao.py
"""

import io
import os

import boto3
import folium
import pandas as pd
import plotly.express as px
import pyarrow.parquet as pq
import requests
import streamlit as st
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv
from streamlit_folium import st_folium

load_dotenv()

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

BUCKET_GOLD = "data2eco-gold"
KEY_GOLD = "gold_biodiversity_trends.parquet"
GEOJSON_URL = (
    "https://raw.githubusercontent.com/codeforamerica/click_that_hood"
    "/master/public/data/brazil-states.geojson"
)

# ---------------------------------------------------------------------------
# Carregamento de dados
# ---------------------------------------------------------------------------


def _get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("ENDPOINT_URL", "http://localhost:4566"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    )


@st.cache_data(show_spinner="Carregando dados da camada Gold…")
def load_mart_data() -> pd.DataFrame:
    """Lê o Parquet da camada Gold no S3/LocalStack."""
    try:
        s3 = _get_s3_client()
        response = s3.get_object(Bucket=BUCKET_GOLD, Key=KEY_GOLD)
        raw = response["Body"].read()
        df = pq.read_table(io.BytesIO(raw)).to_pandas()
        return df
    except (ClientError, NoCredentialsError) as exc:
        st.error(
            f"Erro ao conectar ao S3/LocalStack: {exc}\n\n"
            "Verifique se o Docker está rodando e o arquivo Gold foi gerado com `dbt run`."
        )
        st.stop()


@st.cache_data(show_spinner="Carregando GeoJSON dos estados…")
def load_geojson() -> dict:
    """Baixa o GeoJSON dos estados brasileiros (com cache)."""
    try:
        resp = requests.get(GEOJSON_URL, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        st.warning(
            f"Não foi possível baixar o GeoJSON dos estados: {exc}\n"
            "O mapa não estará disponível."
        )
        return {}


# ---------------------------------------------------------------------------
# Configuração da página
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Biodiversidade — Abelhas Apidae no Brasil",
    page_icon="🐝",
    layout="wide",
)

st.title("🐝 Riqueza de Espécies de Abelhas (Apidae) no Brasil")
st.caption(
    "Comparação entre os períodos **2000-2010** e **2011-2023** · Fonte: GBIF · Família Apidae"
)

# ---------------------------------------------------------------------------
# Carregamento dos dados
# ---------------------------------------------------------------------------

df_raw = load_mart_data()

# ---------------------------------------------------------------------------
# Sidebar — filtros
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Filtros")

    max_riqueza = int(df_raw["riqueza_2011_2023"].max())
    min_riqueza = st.slider(
        "Riqueza mínima em 2011-2023 (nº de espécies)",
        min_value=0,
        max_value=max_riqueza,
        value=0,
    )

    estados_disponiveis = sorted(df_raw["estado"].dropna().unique())
    estados_selecionados = st.multiselect(
        "Filtrar estados (vazio = todos)",
        options=estados_disponiveis,
        default=[],
    )

    st.divider()
    st.caption(
        "**Fonte:** GBIF Occurrence API  \n"
        "**Filtros originais:** `familyKey=4334`, `country=BR`, `year=2000-2023`  \n"
        "**Métrica:** COUNT DISTINCT de nome científico"
    )

# Aplicar filtros
df = df_raw.copy()
df = df[df["riqueza_2011_2023"] >= min_riqueza]
if estados_selecionados:
    df = df[df["estado"].isin(estados_selecionados)]

# ---------------------------------------------------------------------------
# Métricas no topo
# ---------------------------------------------------------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Estados analisados", len(df))

with col2:
    mediana = df["variacao_percentual"].dropna().median()
    st.metric(
        "Variação mediana (%)",
        f"{mediana:+.1f}%",
        delta=f"{mediana:+.1f}%",
        delta_color="normal",
    )

with col3:
    n_declinio = (df["variacao_percentual"].dropna() < 0).sum()
    st.metric(
        "Estados com declínio",
        n_declinio,
        delta=f"{n_declinio} de {len(df)}",
        delta_color="inverse",
    )

st.divider()

# ---------------------------------------------------------------------------
# Abas de visualização
# ---------------------------------------------------------------------------

tab_riqueza, tab_variacao, tab_mapa, tab_tabela = st.tabs(
    ["📊 Riqueza por Estado", "📈 Variação %", "🗺️ Mapa", "📋 Tabela Detalhada"]
)

# ----- Aba 1: Riqueza por Estado -----
with tab_riqueza:
    st.subheader("Riqueza de Espécies por Estado e Período")

    df_barras = (
        df[["estado", "riqueza_2000_2010", "riqueza_2011_2023"]]
        .sort_values("riqueza_2011_2023", ascending=False)
    )
    df_long = df_barras.melt(
        id_vars="estado",
        value_vars=["riqueza_2000_2010", "riqueza_2011_2023"],
        var_name="Período",
        value_name="Riqueza de Espécies",
    )
    df_long["Período"] = df_long["Período"].replace(
        {"riqueza_2000_2010": "2000-2010", "riqueza_2011_2023": "2011-2023"}
    )

    fig_riqueza = px.bar(
        df_long,
        x="estado",
        y="Riqueza de Espécies",
        color="Período",
        barmode="group",
        color_discrete_map={"2000-2010": "#2196F3", "2011-2023": "#FF9800"},
        labels={"estado": "Estado", "Riqueza de Espécies": "Nº de Espécies Distintas"},
        height=480,
    )
    fig_riqueza.update_layout(xaxis_tickangle=-45, legend_title_text="Período")
    st.plotly_chart(fig_riqueza, use_container_width=True)

# ----- Aba 2: Variação % -----
with tab_variacao:
    st.subheader("Variação Percentual da Riqueza de Espécies (2000-2010 → 2011-2023)")

    df_var = df[["estado", "variacao_percentual"]].dropna().sort_values("variacao_percentual")
    df_var["cor"] = df_var["variacao_percentual"].apply(
        lambda v: "Declínio" if v < 0 else "Crescimento"
    )

    fig_var = px.bar(
        df_var,
        x="variacao_percentual",
        y="estado",
        color="cor",
        orientation="h",
        color_discrete_map={"Declínio": "#EF5350", "Crescimento": "#66BB6A"},
        labels={
            "variacao_percentual": "Variação (%)",
            "estado": "Estado",
            "cor": "",
        },
        height=max(400, len(df_var) * 28),
    )
    fig_var.add_vline(x=0, line_color="black", line_width=1)
    fig_var.update_layout(showlegend=True)
    st.plotly_chart(fig_var, use_container_width=True)

# ----- Aba 3: Mapa Folium -----
with tab_mapa:
    st.subheader("Mapa Coroplético — Variação % da Riqueza de Espécies por Estado")

    geojson = load_geojson()

    if not geojson:
        st.info("GeoJSON indisponível. Verifique a conexão com a internet.")
    else:
        df_mapa = df[["estado", "variacao_percentual", "riqueza_2000_2010", "riqueza_2011_2023"]].copy()

        m = folium.Map(location=[-15.0, -55.0], zoom_start=4, tiles="CartoDB positron")

        choropleth = folium.Choropleth(
            geo_data=geojson,
            data=df_mapa,
            columns=["estado", "variacao_percentual"],
            key_on="feature.properties.name",
            fill_color="RdYlGn",
            fill_opacity=0.75,
            line_opacity=0.4,
            nan_fill_color="#d3d3d3",
            legend_name="Variação % da Riqueza de Espécies",
        ).add_to(m)

        # Tooltip com dados detalhados
        df_indexed = df_mapa.set_index("estado")
        for feature in geojson.get("features", []):
            estado_nome = feature["properties"].get("name", "")
            if estado_nome in df_indexed.index:
                row = df_indexed.loc[estado_nome]
                variacao = row["variacao_percentual"]
                variacao_str = (
                    f"{variacao:+.1f}%" if pd.notna(variacao) else "N/D"
                )
                tooltip_html = (
                    f"<b>{estado_nome}</b><br>"
                    f"🐝 Riqueza 2000-2010: <b>{int(row['riqueza_2000_2010'])}</b><br>"
                    f"🐝 Riqueza 2011-2023: <b>{int(row['riqueza_2011_2023'])}</b><br>"
                    f"📈 Variação: <b>{variacao_str}</b>"
                )
                folium.GeoJson(
                    feature,
                    style_function=lambda x: {
                        "fillOpacity": 0,
                        "weight": 0,
                    },
                    tooltip=folium.Tooltip(tooltip_html),
                ).add_to(m)

        st_folium(m, width=900, height=550)

# ----- Aba 4: Tabela -----
with tab_tabela:
    st.subheader("Dados Detalhados por Estado")

    df_display = df.copy()
    df_display = df_display.rename(
        columns={
            "estado": "Estado",
            "riqueza_2000_2010": "Riqueza 2000-2010",
            "riqueza_2011_2023": "Riqueza 2011-2023",
            "variacao_percentual": "Variação (%)",
        }
    )
    df_display = df_display.sort_values("Variação (%)", ascending=True)

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Variação (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Riqueza 2000-2010": st.column_config.NumberColumn(format="%d"),
            "Riqueza 2011-2023": st.column_config.NumberColumn(format="%d"),
        },
    )

    csv = df_display.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Baixar CSV",
        data=csv,
        file_name="riqueza_especies_apidae.csv",
        mime="text/csv",
    )
