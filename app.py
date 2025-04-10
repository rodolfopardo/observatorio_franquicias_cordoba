import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Observatorio de Franquicias – Córdoba", layout="wide")

USUARIOS_VALIDOS = {
    "rodolfopardo": "1234",
    "jp": "1234",
    "brian": "1234",
    "invitado": "searchmas"
}

def login():
    st.image("https://media.licdn.com/dms/image/v2/C4E0BAQEI7gHrMu33ug/company-logo_200_200/company-logo_200_200/0/1630567809960/search_mas_logo?e=1749686400&v=beta&t=gX3L1x9Yl9Xg8iASJ1_mil9GNfa6-hLM9JglCP2b3mo", width=200)
    st.title("🔐 Observatorio de Franquicias – Córdoba")
    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Iniciar sesión"):
        if user in USUARIOS_VALIDOS and password == USUARIOS_VALIDOS[user]:
            st.session_state['logged_in'] = True
            st.session_state['user'] = user
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

if 'logged_in' not in st.session_state:
    login()
    st.stop()

# --- CARGA Y LIMPIEZA DE DATOS ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.image("https://media.licdn.com/dms/image/v2/C4E0BAQEI7gHrMu33ug/company-logo_200_200/company-logo_200_200/0/1630567809960/search_mas_logo?e=1749686400&v=beta&t=gX3L1x9Yl9Xg8iASJ1_mil9GNfa6-hLM9JglCP2b3mo", width=120)
with col_title:
    st.title("📊 Observatorio de Franquicias – Córdoba")

st.sidebar.markdown(f"👤 Sesión iniciada como: `{st.session_state.get('user', '')}`")

@st.cache_data
def cargar_datos():
    df = pd.read_csv("https://drive.google.com/uc?id=162YQgYfv4cbL3yudA-hNysDp3V4MqUgI")
    df['title'] = df['title'].astype(str)
    df['addressPreview'] = df['addressPreview'].astype(str)
    df = df[df['addressPreview'].str.contains(r'c[oó]rdoba', case=False, na=False)]

    total_original = len(df)
    total_cordoba = len(df)
    eliminados = total_original - total_cordoba

    df['title_normalizado'] = df['title'].str.lower().str.replace(r'[^a-z0-9 ]', '', regex=True)
    marca_counts = df['title_normalizado'].value_counts()
    df['es_franquiciado'] = df['title_normalizado'].isin(marca_counts[marca_counts > 1].index)

    return df, eliminados

df, registros_fuera_cordoba = cargar_datos()

if registros_fuera_cordoba > 0:
    st.warning(f"⚠️ Se eliminaron {registros_fuera_cordoba} registros que no pertenecen a Córdoba.")

# --- PANEL GENERAL ---
st.markdown("### Panel General")

total_filas = len(df)
total_columnas = df.shape[1]
total_marcas = df['title'].nunique()
marcas_franquiciadas = df[df['es_franquiciado']]['title'].nunique()
marcas_no_franquiciadas = total_marcas - marcas_franquiciadas

porc_franq = (marcas_franquiciadas / total_marcas) * 100 if total_marcas > 0 else 0
porc_no_franq = 100 - porc_franq

col1, col2, col3, col4 = st.columns(4)
col1.metric("Datos analizados", total_filas)
col2.metric("Variables analizadas", total_columnas)
col3.metric("Candidatos (franquicias)", f"{marcas_franquiciadas} ({porc_franq:.1f}%)")
col4.metric("No candidatos (negocios comunes)", f"{marcas_no_franquiciadas} ({porc_no_franq:.1f}%)")

st.markdown("### Distribución de tipos de marcas")
pie_df = pd.DataFrame({
    'Tipo': ['Candidatos (franquicias)', 'No candidatos (negocios comunes)'],
    'Cantidad': [marcas_franquiciadas, marcas_no_franquiciadas]
})
fig_pie = px.pie(pie_df, names='Tipo', values='Cantidad', title='Distribución de tipos de marcas')
fig_pie.update_layout(
    height=500,
    title_font_size=20,
    legend_font_size=14
)
st.plotly_chart(fig_pie, use_container_width=True)

# --- FILTROS ---
st.markdown("### Filtros")

tipo_cluster = st.radio("¿Qué tipo de negocios querés analizar?", ['Candidatos (franquicias)', 'No candidatos (negocios comunes)'])
es_franquiciado = True if tipo_cluster == 'Candidatos (franquicias)' else False

df_filtrado_tipo = df[df['es_franquiciado'] == es_franquiciado]

marcas_disponibles = (
    df_filtrado_tipo['title']
    .value_counts()
    .sort_values(ascending=False)
    .index
    .tolist()
)

marca_seleccionada = st.selectbox("Seleccioná una marca", ["Todas"] + marcas_disponibles)
if marca_seleccionada != "Todas":
    df_filtrado = df_filtrado_tipo[df_filtrado_tipo['title'] == marca_seleccionada]
else:
    df_filtrado = df_filtrado_tipo.copy()

# --- FILTRO POR KEYWORD ---
keywords_disponibles = (
    df_filtrado['keyword']
    .dropna()
    .astype(str)
    .str.strip()
    .str.lower()
    .value_counts()
    .sort_values(ascending=False)
    .index
    .tolist()
)

keyword_seleccionada = st.selectbox("Filtrar por keyword", ["Todas"] + keywords_disponibles)
if keyword_seleccionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado['keyword'].str.lower().str.strip() == keyword_seleccionada]

# --- SECCIÓN TOP 10 ---
st.markdown("### Top 10 negocios destacados")

if es_franquiciado:
    top_direcciones = (
        df_filtrado.groupby('title')
        .size()
        .reset_index(name='cantidad_direcciones')
        .sort_values(by='cantidad_direcciones', ascending=False)
        .head(10)
    )
    st.markdown("#### 🏪 Candidatos con más direcciones")
    st.dataframe(top_direcciones[['title', 'cantidad_direcciones']], use_container_width=True)

else:
    if 'reviews' in df_filtrado.columns and 'stars' in df_filtrado.columns:
        df_temp = df_filtrado.copy()
        df_temp['reviews'] = pd.to_numeric(df_temp['reviews'], errors='coerce')
        df_temp['stars'] = pd.to_numeric(df_temp['stars'], errors='coerce')
        df_validos = df_temp.dropna(subset=['reviews', 'stars'])

        if not df_validos.empty:
            top_reviews = (
                df_validos.groupby('title')
                .agg({
                    'reviews': 'sum',
                    'stars': 'mean'
                })
                .reset_index()
                .sort_values(by=['reviews', 'stars'], ascending=[False, False])
                .head(10)
            )
            st.markdown("#### 🌟 Negocios comunes con más reviews")
            st.dataframe(top_reviews[['title', 'reviews', 'stars']], use_container_width=True)
        else:
            st.info("No hay datos válidos de 'reviews' y 'stars' para generar el ranking.")
    else:
        st.info("No existen columnas 'reviews' o 'stars' en el CSV.")

# --- VISUALIZACIÓN DE KEYWORDS O DISTRIBUCIÓN DE MARCAS SEGÚN KEYWORD ---
if keyword_seleccionada == "Todas":
    st.markdown("### 🌞 Visualización jerárquica de keywords (Sunburst optimizado)")
    
    if 'keyword' in df_filtrado.columns:
        keywords = df_filtrado['keyword'].dropna().astype(str).str.strip().str.lower()
        top_keywords = Counter(keywords).most_common(10)
        
        if top_keywords:
            labels = [kw for kw, _ in top_keywords]
            values = [v for _, v in top_keywords]
            parents = [''] * len(labels)

            fig = go.Figure(go.Sunburst(
                labels=labels,
                parents=parents,
                values=values,
                branchvalues="total",
                textinfo="label+value+percent entry",
                insidetextorientation='radial',
                hovertemplate='<b>%{label}</b><br>Frecuencia: %{value}<br>%{percentEntry:.1%}',
            ))

            fig.update_layout(
                title="Top 10 keywords más frecuentes",
                margin=dict(t=50, l=0, r=0, b=0),
                height=550,
                uniformtext=dict(minsize=12, mode='show')
            )

            st.plotly_chart(fig, use_container_width=True)

else:
    st.markdown("### 📈 Participación de marcas para la keyword seleccionada")

    marcas_keyword = (
        df_filtrado['title']
        .value_counts(normalize=True)
        .mul(100)
        .reset_index()
        .rename(columns={'index': 'Marca', 'title': 'Porcentaje'})
        .sort_values(by='Porcentaje', ascending=False)
    )

    fig_bar = px.bar(
        marcas_keyword,
        x='Marca',
        y='Porcentaje',
        text='Porcentaje',
        labels={'Porcentaje': '% de negocios con esta keyword'},
        title=f"% de participación por marca para la keyword: '{keyword_seleccionada}'"
    )
    fig_bar.update_layout(
        height=500,
        xaxis_tickangle=-45,
        yaxis_ticksuffix="%",
        title_font_size=20
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# --- TABLA FINAL CON FILTROS APLICADOS ---
st.markdown("### 📋 Tabla final con todos los datos")
df_final = df_filtrado.drop_duplicates(subset=['addressPreview'])
st.dataframe(df_final, use_container_width=True)

csv = df_final.to_csv(index=False).encode('utf-8')
st.download_button("📥 Descargar tabla filtrada", csv, "franquicias_filtradas.csv", "text/csv")

# --- LOGOUT ---
st.markdown("---")
if st.button("🔓 Cerrar sesión"):
    st.session_state.clear()
    st.rerun()
