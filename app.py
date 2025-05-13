import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Observatorio de Comercios – Córdoba", layout="wide")

USUARIOS_VALIDOS = {
    "rodolfopardo": "1234",
    "jp": "1234",
    "brian": "1234",
    "invitado": "searchmas",
    "observatorio": "franquicia"
}

def login():
    st.image("https://media.licdn.com/dms/image/v2/C4E0BAQEI7gHrMu33ug/company-logo_200_200/company-logo_200_200/0/1630567809960/search_mas_logo?e=2147483647&v=beta&t=XUaWkB-j3eCKUWCuySIzXe5s42ScA4dstIVrYVbgl4s", width=200)
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

# --- ENCABEZADO ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.image("https://media.licdn.com/dms/image/v2/C4E0BAQEI7gHrMu33ug/company-logo_200_200/company-logo_200_200/0/1630567809960/search_mas_logo?e=2147483647&v=beta&t=XUaWkB-j3eCKUWCuySIzXe5s42ScA4dstIVrYVbgl4s", width=120)
with col_title:
    st.title("Observatorio de Comercios – Córdoba")

st.sidebar.markdown(f"👤 Sesión iniciada como: `{st.session_state.get('user', '')}`")

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
    url = "https://drive.google.com/uc?export=download&id=19yEmueLePXiPZVV9fYYQWbLhMP9N6AzO"
    df = pd.read_csv(url)
    df["LOCALIDAD"] = df["addressPreview"].astype(str).str.extract(r",\s*([^,]+)$")
    df = df[["title_limpio", "keyword", "addressPreview", "LOCALIDAD"]].copy()
    df.columns = ["COMERCIO", "RUBRO", "DIRECCIÓN", "LOCALIDAD"]
    df = df.drop_duplicates(subset=["DIRECCIÓN"])
    return df

import re

import re

# --- CARGA Y FILTRO DE DATOS BASE ---
df = cargar_datos()

# --- FILTRO DE MARCAS POPULARES ---
st.sidebar.markdown("### Filtro inteligente de datos")
filtrar_populares = st.sidebar.radio("¿Filtrar marcas populares?", ["No", "Sí"], horizontal=True)

# Lista de comercios populares
patrones_conocidos = [
    "grido", "mcdonald", "burger king", "secco", "extra supermercado",
    "jumbo", "carrefour", "lavarap", "pintecord", "farmacity", "freddo",
    "naranja", "sodimac", "tupi", "easy", "tarjeta naranja", "galicia",
    "banco de la nacion", "bancor", "western union", "pago facil", "rapipago",
    "laverap", "shell", "ypf", "PIZZERIA popular"
]

def es_marca_conocida(nombre):
    nombre = str(nombre).lower()
    return any(re.search(pat, nombre) for pat in patrones_conocidos)

# Aplicar el filtro popular primero para generar base real
df_base = df.copy()
if filtrar_populares == "Sí":
    df_base = df_base[~df_base["COMERCIO"].apply(es_marca_conocida)]

# --- ORDEN PARA FILTROS (ya sobre df_base) ---
orden_marcas = df_base["COMERCIO"].value_counts().reset_index()
orden_marcas.columns = ["COMERCIO", "CANTIDAD"]

orden_rubros = df_base["RUBRO"].value_counts().reset_index()
orden_rubros.columns = ["RUBRO", "CANTIDAD"]

# --- FILTROS MULTI ---
st.sidebar.title("Filtros")

comercios_ordenados = orden_marcas["COMERCIO"].tolist()
rubros_ordenados = orden_rubros["RUBRO"].tolist()

marcas_seleccionadas = st.sidebar.multiselect("MARCA", options=comercios_ordenados, default=[])
rubros_seleccionadas = st.sidebar.multiselect("RUBRO", options=rubros_ordenados, default=[])

# --- APLICAR FILTROS MULTI SOBRE BASE FILTRADA ---
df_filtrado = df_base.copy()

if marcas_seleccionadas:
    df_filtrado = df_filtrado[df_filtrado["COMERCIO"].isin(marcas_seleccionadas)]

if rubros_seleccionadas:
    df_filtrado = df_filtrado[df_filtrado["RUBRO"].isin(rubros_seleccionadas)]


# --- KPI PRINCIPAL ---
st.metric("🧾 Comercios analizados", value=f"{len(df_filtrado):,}")

# --- GRÁFICO 1: BARRAS COMERCIO ---
top_comercios = df_filtrado["COMERCIO"].value_counts().head(20).reset_index()
top_comercios.columns = ["COMERCIO", "CANTIDAD"]
fig1 = px.bar(
    top_comercios,
    x="CANTIDAD",
    y="COMERCIO",
    orientation="h",
    text_auto=True,
    title="Cantidad de direcciones por Marca"
)
fig1.update_layout(
    height=600,
    yaxis={'categoryorder': 'total ascending'},
    margin=dict(t=40, l=20, r=20, b=20)
)
fig1.update_traces(textfont_size=16) 
fig1.update_traces(textposition='outside')





# --- VISUALIZACIÓN VERTICAL ---
st.plotly_chart(fig1, use_container_width=True)


# --- DETALLE TABLA ---
st.markdown("### 📋 Detalles de comercios")
st.dataframe(df_filtrado[["COMERCIO", "RUBRO", "DIRECCIÓN", "LOCALIDAD"]].sort_values(by="COMERCIO"), use_container_width=True)

# --- DESCARGA CSV ---
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
