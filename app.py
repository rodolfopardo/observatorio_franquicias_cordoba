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
    df['title_normalizado'] = df['title'].str.lower().str.replace(r'[^a-z0-9 ]', '', regex=True)
    marca_counts = df['title_normalizado'].value_counts()
    df['es_franquiciado'] = df['title_normalizado'].isin(marca_counts[marca_counts > 1].index)
    return df

df = cargar_datos()

# --- PANEL GENERAL ---
st.markdown("### Panel General")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Datos analizados", len(df))
col2.metric("Variables analizadas", df.shape[1])
total_marcas = df['title'].nunique()
marcas_franquiciadas = df[df['es_franquiciado']]['title'].nunique()
marcas_no_franquiciadas = total_marcas - marcas_franquiciadas
col3.metric("Marcas con franquicia", f"{marcas_franquiciadas} ({(marcas_franquiciadas/total_marcas*100):.1f}%)")
col4.metric("Marcas sin franquicia", f"{marcas_no_franquiciadas} ({(marcas_no_franquiciadas/total_marcas*100):.1f}%)")

st.markdown("### Distribución de Marcas")
pie_df = pd.DataFrame({
    'Tipo': ['Marcas con franquicias', 'Marcas sin franquicias'],
    'Cantidad': [marcas_franquiciadas, marcas_no_franquiciadas]
})
st.plotly_chart(px.pie(pie_df, names='Tipo', values='Cantidad', title='Distribución de marcas únicas'), use_container_width=True)

# --- FILTROS ---
st.markdown("### Filtros")
tipo_cluster = st.radio("¿Qué tipo de negocios te gustaría analizar?", ['Franquiciados', 'No franquiciados'])
es_franquiciado = tipo_cluster == 'Franquiciados'
df_filtrado_tipo = df[df['es_franquiciado'] == es_franquiciado]

marcas_disponibles = df_filtrado_tipo['title'].value_counts().index.tolist()
marcas_seleccionadas = st.multiselect("Seleccioná una o más marcas", marcas_disponibles)

df_filtrado = df_filtrado_tipo[df_filtrado_tipo['title'].isin(marcas_seleccionadas)] if marcas_seleccionadas else df_filtrado_tipo.copy()

keywords_disponibles = df_filtrado['keyword'].dropna().astype(str).str.strip().str.lower().value_counts().index.tolist()
keywords_seleccionadas = st.multiselect("Filtrar por una o más keywords", keywords_disponibles)

if keywords_seleccionadas:
    df_filtrado = df_filtrado[df_filtrado['keyword'].str.lower().str.strip().isin(keywords_seleccionadas)]

# --- TOP 10 ---
st.markdown("### Top 10 negocios destacados")
if es_franquiciado:
    top = df_filtrado['title'].value_counts().reset_index()
    top.columns = ['Marca', 'Cantidad de apariciones']
    st.markdown("#### 🏪 Franquicias con más apariciones")
    st.dataframe(top.head(10), use_container_width=True)
else:
    if {'reviews', 'stars'}.issubset(df_filtrado.columns):
        df_filtrado['reviews'] = pd.to_numeric(df_filtrado['reviews'], errors='coerce')
        df_filtrado['stars'] = pd.to_numeric(df_filtrado['stars'], errors='coerce')
        top = df_filtrado.groupby('title').agg({'reviews': 'sum', 'stars': 'mean'}).reset_index()
        top.columns = ['Marca', 'reviews', 'stars']
        st.markdown("#### 🌟 Negocios no franquiciados con más reviews")
        st.dataframe(top.sort_values(by=['reviews', 'stars'], ascending=[False, False]).head(10), use_container_width=True)
    else:
        st.info("No hay datos suficientes para mostrar reviews o estrellas.")

# --- VISUALIZACIÓN ---
st.markdown("### 🌞 Visualización jerárquica de keywords o marcas")
if marcas_seleccionadas:
    top_keywords = Counter(df_filtrado['keyword'].dropna().str.lower().str.strip()).most_common(10)
    if top_keywords:
        labels, values = zip(*top_keywords)
        st.plotly_chart(go.Figure(go.Sunburst(labels=labels, parents=['']*len(labels), values=values)), use_container_width=True)
elif keywords_seleccionadas:
    top_marcas = Counter(df_filtrado['title'].dropna().str.strip()).most_common(10)
    df_bar = pd.DataFrame(top_marcas, columns=['Marca', 'Apariciones'])
    df_bar['% Representación'] = (df_bar['Apariciones'] / df_bar['Apariciones'].sum() * 100).round(2)
    st.plotly_chart(px.bar(df_bar.sort_values('% Representación'), x='% Representación', y='Marca', orientation='h', text='% Representación'), use_container_width=True)
else:
    top_keywords = Counter(df_filtrado['keyword'].dropna().str.lower().str.strip()).most_common(10)
    if top_keywords:
        labels, values = zip(*top_keywords)
        st.plotly_chart(go.Figure(go.Sunburst(labels=labels, parents=['']*len(labels), values=values)), use_container_width=True)

# --- TABLA FINAL ---
st.markdown("### 📋 Tabla final con todos los datos")
columnas_a_excluir = [
    'client', 'accountName', 'locationId', 'locationName', 'locationCity',
    'locationState', 'type', 'createdAt', 'title_normalizado', 'es_franquiciado'
]
df_final = df_filtrado.drop(columns=[c for c in columnas_a_excluir if c in df_filtrado.columns], errors='ignore').drop_duplicates(subset=['addressPreview'])
if 'stars' in df_final.columns:
    df_final['stars'] = pd.to_numeric(df_final['stars'], errors='coerce').round(2)
st.dataframe(df_final, use_container_width=True)
st.download_button("📥 Descargar tabla filtrada", df_final.to_csv(index=False).encode('utf-8'), "franquicias_filtradas.csv", "text/csv")

# --- LOGOUT ---
st.markdown("---")
if st.button("🔓 Cerrar sesión"):
    st.session_state.clear()
    st.rerun()
