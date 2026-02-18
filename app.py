import streamlit as st
import pandas as pd

# ────────────────────────────────────────────────
# CONFIGURACIÓN
# ────────────────────────────────────────────────
st.set_page_config(page_title="InsideBet", layout="wide")

# SUSTITUYE AQUÍ
USER = "InsideBet" 
REPO = "picks-top-web"
# La ruta Raw correcta según tu captura:
BASE_URL = f"https://raw.githubusercontent.com/{USER}/{REPO}/main/datos_fbref"

LIGAS = {
    "PL": "Premier League",
    # Agrega las demás siguiendo el mismo formato
}

# Este mapeo debe coincidir EXACTAMENTE con el sufijo de tus archivos .xlsx
MAPEO_ARCHIVOS = {
    "Premier League": "Premier_League",
}

BANDERAS = {
    "PL": "https://i.postimg.cc/7PcwYbk1/1.png",
}

# ────────────────────────────────────────────────
# ESTILO (Tu diseño original)
# ────────────────────────────────────────────────
st.markdown("""<style>.stApp { background-color: #0e1117; color: #e5e7eb; }</style>""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center; margin-top:15px; margin-bottom:20px;">
    <img src="https://i.postimg.cc/hPkSPNcT/Sin-titulo-2.png" width="280"><br>
    <p style="font-family: 'Montserrat', sans-serif; font-size:18px; font-weight:500; color:#e5e7eb; margin-top:10px;">
       Partidos & Estadísticas
    </p>
</div>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# FUNCIONES DE CARGA
# ────────────────────────────────────────────────
@st.cache_data(ttl=600)
def cargar_cartelera(nombre_archivo):
    # Intentamos cargar CARTELERA_PROXIMOS_...
    url = f"{BASE_URL}/CARTELERA_PROXIMOS_{nombre_archivo}.xlsx"
    try:
        return pd.read_excel(url)
    except Exception as e:
        return None

# ────────────────────────────────────────────────
# INTERFAZ POR TABS
# ────────────────────────────────────────────────
tab_objects = st.tabs(list(LIGAS.values()))

for i, (code, nombre_pantalla) in enumerate(LIGAS.items()):
    with tab_objects[i]:
        st.markdown(f"""
        <div style="display:flex; align-items:center; color:#e5e7eb; font-size:22px; font-weight:500; margin-bottom:10px;">
            <img src="{BANDERAS[code]}" width="30" style="vertical-align:middle; margin-right:10px;">
            <span>{nombre_pantalla}</span>
        </div>
        """, unsafe_allow_html=True)

        archivo_sufijo = MAPEO_ARCHIVOS.get(nombre_pantalla)
        df = cargar_cartelera(archivo_sufijo)

        if df is None:
            st.error(f"No se pudo encontrar el archivo en: {BASE_URL}/CARTELERA_PROXIMOS_{archivo_sufijo}.xlsx")
        elif df.empty:
            st.warning("El archivo está vacío.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
