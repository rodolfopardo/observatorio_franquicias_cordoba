import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Observatorio de Comercios – Córdoba", layout="wide")

USUARIOS_VALIDOS = {
    "rodolfopardo": "1234",
    "jp": "1234",
    "brian": "1234",
    "invitado": "searchmas"
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

df = cargar_datos()

# --- ORDEN PARA FILTROS ---
orden_marcas = df["COMERCIO"].value_counts().reset_index()
orden_marcas.columns = ["COMERCIO", "CANTIDAD"]

orden_rubros = df["RUBRO"].value_counts().reset_index()
orden_rubros.columns = ["RUBRO", "CANTIDAD"]

# --- FILTROS MULTI + POPULARES ---
import re

st.sidebar.title("Filtros")

comercios_ordenados = orden_marcas["COMERCIO"].tolist()
rubros_ordenados = orden_rubros["RUBRO"].tolist()

# MULTISELECCIÓN
marcas_seleccionadas = st.sidebar.multiselect("MARCA", options=comercios_ordenados, default=[])
rubros_seleccionados = st.sidebar.multiselect("RUBRO", options=rubros_ordenados, default=[])

# FILTRO MARCAS POPULARES
st.sidebar.markdown("¿Querés ver solo marcas conocidas o populares?")
filtrar_populares = st.sidebar.radio("Filtrar marcas populares", ["No", "Sí"], horizontal=True)

# Lista de patrones populares
patrones_conocidos = [
    "grido", "mcdonald", "burger king", "secco", "extra supermercado",
    "jumbo", "carrefour", "lavarap", "pintecord", "farmacity", "freddo",
    "naranja", "sodimac", "tupi", "easy", "tarjeta naranja", "galicia",
    "banco de la nacion", "bancor", "western union", "pago facil", "rapipago"
]

def es_marca_conocida(nombre):
    nombre = str(nombre).lower()
    return any(re.search(pat, nombre) for pat in patrones_conocidos)

# APLICAR FILTROS
df_filtrado = df.copy()

if marcas_seleccionadas:
    df_filtrado = df_filtrado[df_filtrado["COMERCIO"].isin(marcas_seleccionadas)]

if rubros_seleccionados:
    df_filtrado = df_filtrado[df_filtrado["RUBRO"].isin(rubros_seleccionados)]

if filtrar_populares == "Sí":
    df_filtrado = df_filtrado[df_filtrado["COMERCIO"].apply(es_marca_conocida)]
else:
    df_filtrado = df_filtrado[~df_filtrado["COMERCIO"].apply(es_marca_conocida)]


# --- KPI PRINCIPAL ---
st.metric("🧾 Comercios analizados", value=f"{len(df_filtrado):,}")

# --- GRÁFICO 1: BARRAS COMERCIO ---
top_comercios = df_filtrado["COMERCIO"].value_counts().head(15).reset_index()
top_comercios.columns = ["COMERCIO", "CANTIDAD"]
fig1 = px.bar(
    top_comercios,
    x="CANTIDAD",
    y="COMERCIO",
    orientation="h",
    text_auto=True,
    title="Comercios por Marca"
)
fig1.update_layout(
    height=450,
    yaxis={'categoryorder': 'total ascending'},
    margin=dict(t=40, l=20, r=20, b=20)
)

# --- GRÁFICO 2: TREEMAP RUBROS ---
top_rubros = df_filtrado["RUBRO"].value_counts().head(20).reset_index()
top_rubros.columns = ["RUBRO", "CANTIDAD"]
fig2 = px.treemap(
    top_rubros,
    path=["RUBRO"],
    values="CANTIDAD",
    title="Top 20 - Comercios por Tipo"
)
fig2.update_traces(textinfo="label+value")
fig2.update_layout(margin=dict(t=40, l=20, r=20, b=20), height=500)

# --- VISUALIZACIÓN VERTICAL ---
st.plotly_chart(fig1, use_container_width=True)
st.plotly_chart(fig2, use_container_width=True)

# --- DETALLE TABLA ---
st.markdown("### 📋 Detalle de comercios")
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
