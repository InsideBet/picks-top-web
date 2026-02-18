import streamlit as st
import pandas as pd

# ────────────────────────────────────────────────
# CONFIGURACIÓN
# ────────────────────────────────────────────────
st.set_page_config(page_title="InsideBet", layout="wide")

USER = "InsideBet" 
REPO = "picks-top-web"
BASE_URL = f"https://raw.githubusercontent.com/{USER}/{REPO}/main/datos_fbref"

LIGAS = {
    "PL": "Premier League",
    "PD": "La Liga",
    "SA": "Serie A",
}

MAPEO_ARCHIVOS = {
    "Premier League": "Premier_League",
    "La Liga": "La_Liga",
    "Serie A": "Serie_A",
}

# ────────────────────────────────────────────────
# ESTILO Y SCROLL GLOBAL (AJUSTE PARA PC)
# ────────────────────────────────────────────────
st.markdown("""
<style>
    /* Permite que el navegador maneje el scroll naturalmente en PC */
    html, body, [data-testid="stAppViewContainer"] {
        overflow-y: auto !important;
    }
    
    [data-testid="stMainViewContainer"] {
        overflow: visible !important;
    }

    .block-container {
        max-width: 95% !important;
        padding-bottom: 5rem !important;
    }

    /* Colores base */
    .stApp { background-color: #0e1117; color: #e5e7eb; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# FUNCIONES
# ────────────────────────────────────────────────
@st.cache_data(ttl=300)
def cargar_excel(ruta_archivo):
    url = f"{BASE_URL}/{ruta_archivo}"
    try:
        df = pd.read_excel(url)
        # Limpieza de filas vacías
        for col in ['Local', 'Home', 'Squad', 'Equipo']:
            if col in df.columns:
                df = df.dropna(subset=[col])
                break
        return df
    except:
        return None

# ────────────────────────────────────────────────
# INTERFAZ
# ────────────────────────────────────────────────
tab_objects = st.tabs(list(LIGAS.values()))

for i, (code, nombre_pantalla) in enumerate(LIGAS.items()):
    with tab_objects[i]:
        archivo_sufijo = MAPEO_ARCHIVOS.get(nombre_pantalla)
        
        # 1. Cargar datos
        df_stats = cargar_excel(f"RESUMEN_STATS_{archivo_sufijo}.xlsx")

        # --- Lógica de Ordenamiento por Puntos ---
        if df_stats is not None:
            # Buscamos la columna de puntos (FBref suele usar 'Pts')
            col_pts = next((c for c in df_stats.columns if 'Pts' in c), None)
            if col_pts:
                # Convertimos a numérico por seguridad y ordenamos de mayor a menor
                df_stats[col_pts] = pd.to_numeric(df_stats[col_pts], errors='coerce')
                df_stats = df_stats.sort_values(by=col_pts, ascending=False)

        # 2. Layout
        col_btn1, col_btn2 = st.columns([1, 2])
        with col_btn1:
            mostrar_fixture = st.button(f"📅 Fixture", key=f"f_{code}")
        with col_btn2:
            if df_stats is not None:
                col_eq = next((c for c in df_stats.columns if c in ['Equipo', 'Squad', 'Unnamed: 1']), df_stats.columns[1])
                lista_equipos = sorted([str(x) for x in df_stats[col_eq].unique() if str(x) != 'nan'])
                equipo_sel = st.selectbox("🔍 Analizar Equipo:", ["Seleccionar..."] + lista_equipos, key=f"s_{code}")
            else:
                equipo_sel = "Seleccionar..."

        st.divider()

        # 3. Visualización
        if equipo_sel != "Seleccionar...":
            nombre_file = equipo_sel.replace(" ", "_")
            df_ind = cargar_excel(f"Ligas_Equipos/{nombre_file}.xlsx")
            if df_ind is not None:
                # height=None quita el scroll interno de la tabla y habilita el de la PC
                st.dataframe(df_ind, use_container_width=True, hide_index=True, height=None)

        elif mostrar_fixture:
            df_fix = cargar_excel(f"CARTELERA_PROXIMOS_{archivo_sufijo}.xlsx")
            if df_fix is not None:
                st.dataframe(df_fix, use_container_width=True, hide_index=True, height=None)

        else:
            if df_stats is not None:
                st.subheader("🏆 Clasificación Actualizada")
                # Mostramos la tabla ya ordenada por Pts
                st.dataframe(df_stats, use_container_width=True, hide_index=True, height=None)
