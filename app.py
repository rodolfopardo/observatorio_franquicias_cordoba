# Código actualizado que incluye:
# - botón de descarga de tabla
# - gráfico SearchMas: barplot + treemap
# - logging principal y login de usuario

import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Observatorio de Comercios – Córdoba", layout="wide")

# --- LOGIN ---
USUARIOS_VALIDOS = {
    "rodolfopardo": "1234",
    "jp": "1234",
    "brian": "1234",
    "invitado": "searchmas"
}

def login():
    st.image("https://media.licdn.com/dms/image/v2/C4E0BAQEI7gHrMu33ug/company-logo_200_200/company-logo_200_200/0/1630567809960/search_mas_logo", width=200)
    st.title("Observatorio de Comercios – Córdoba")
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

# --- HEADER ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.image("https://media.licdn.com/dms/image/v2/C4E0BAQEI7gHrMu33ug/company-logo_200_200/company-logo_200_200/0/1630567809960/search_mas_logo", width=120)
with col_title:
    st.title("Observatorio de Comercios – Córdoba")

st.sidebar.markdown(f"👤 Sesión iniciada como: `{st.session_state.get('user', '')}`")

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
    df = pd.read_csv("https://drive.google.com/uc?export=download&id=19yEmueLePXiPZVV9fYYQWbLhMP9N6AzO")
    df = df[["title_limpio", "keyword", "addressPreview"]].copy()
    df.columns = ["COMERCIO", "RUBRO", "DIRECCIÓN"]
    return df

df = cargar_datos()

# --- FILTROS DINÁMICOS ---
st.sidebar.title("Filtros")
comercios = sorted(df["COMERCIO"].dropna().unique())
rubros = sorted(df["RUBRO"].dropna().unique())

comercio_sel = st.sidebar.selectbox("MARCA", options=["Todas"] + comercios)
rubro_sel = st.sidebar.selectbox("RUBRO", options=["Todas"] + rubros)

df_filtrado = df.copy()
if comercio_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado["COMERCIO"] == comercio_sel]
if rubro_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado["RUBRO"] == rubro_sel]

# --- KPI PRINCIPAL ---
st.metric("🧾 Comercios", value=f"{len(df_filtrado):,}")

# --- VISUALIZACIÓN: COMERCIOS POR MARCA ---
top_comercios = df_filtrado["COMERCIO"].value_counts().head(15).reset_index()
top_comercios.columns = ["COMERCIO", "CANTIDAD"]
fig1 = px.bar(top_comercios, x="CANTIDAD", y="COMERCIO", orientation="h", title="Comercios por Marca")
fig1.update_layout(height=400, yaxis={'categoryorder':'total ascending'})

# --- VISUALIZACIÓN: COMERCIOS POR RUBRO ---
top_rubros = df_filtrado["RUBRO"].value_counts().head(20).reset_index()
top_rubros.columns = ["RUBRO", "CANTIDAD"]
fig2 = px.treemap(top_rubros, path=["RUBRO"], values="CANTIDAD", title="Top 20 - Comercios por Tipo")
fig2.update_layout(margin=dict(t=30, l=10, r=10, b=10), height=400)

# --- LAYOUT CON GRÁFICOS ---
col1, col2 = st.columns([1, 2])
with col1:
    st.plotly_chart(fig1, use_container_width=True)
with col2:
    st.plotly_chart(fig2, use_container_width=True)

# --- DETALLE DE COMERCIOS ---
st.markdown("### 📋 Detalle Comercios")
st.dataframe(df_filtrado.sort_values(by="COMERCIO"), use_container_width=True)

# --- BOTÓN DE DESCARGA ---
csv = df_filtrado.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Descargar tabla filtrada",
    data=csv,
    file_name="comercios_filtrados.csv",
    mime="text/csv"
)

# --- LOGOUT ---
st.markdown("---")
if st.button("🔓 Cerrar sesión"):
    st.session_state.clear()
    st.rerun()
