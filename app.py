import streamlit as st
import pandas as pd

# ────────────────────────────────────────────────
# CONFIGURACIÓN
# ────────────────────────────────────────────────
st.set_page_config(page_title="InsideBet", layout="wide")

USER = "InsideBet" 
REPO = "picks-top-web"
BASE_URL = f"https://raw.githubusercontent.com/{USER}/{REPO}/main/datos_fbref"

# Lista completa de tus ligas (se activarán según existan los archivos)
LIGAS = {
    "PL": "Premier League",
    "PD": "La Liga",
    "SA": "Serie A",
    "BL1": "Bundesliga",
    "FL1": "Ligue 1",
    "PPL": "Primeira Liga",
    "DED": "Eredivisie",
    "CL": "Champions League"
}

MAPEO_ARCHIVOS = {
    "Premier League": "Premier_League",
    "La Liga": "La_Liga",
    "Serie A": "Serie_A",
    "Bundesliga": "Bundesliga",
    "Ligue 1": "Ligue_1",
    "Primeira Liga": "Primeira_Liga",
    "Eredivisie": "Eredivisie",
    "Champions League": "Champions_League"
}

BANDERAS = {
    "PL": "https://i.postimg.cc/7PcwYbk1/1.png",
    "PD": "https://i.postimg.cc/75d5mMQ2/8.png",
    "SA": "https://i.postimg.cc/mzxTFmpm/4.png",
    "BL1": "https://i.postimg.cc/5X09cYFn/3.png",
    "FL1": "https://i.postimg.cc/jnbqBMz2/2.png",
    "PPL": "https://i.postimg.cc/ZBr4P61R/5.png",
    "DED": "https://i.postimg.cc/tnkbwpqv/6.png",
    "CL": "https://i.postimg.cc/zb1V1DNy/7.png"
}

# ────────────────────────────────────────────────
# ESTILO Y LOGO
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
# FUNCIONES DE CARGA Y LIMPIEZA
# ────────────────────────────────────────────────
@st.cache_data(ttl=600)
def cargar_excel(ruta_archivo):
    try:
        df = pd.read_excel(f"{BASE_URL}/{ruta_archivo}")
        # LIMPIEZA: Eliminamos filas donde todas las columnas sean NaN o falte el equipo Local
        # Esto quita los espacios en blanco que mencionaste
        col_local = 'Local' if 'Local' in df.columns else 'Home'
        df = df.dropna(subset=[col_local]) 
        return df
    except:
        return None

# ────────────────────────────────────────────────
# INTERFAZ
# ────────────────────────────────────────────────
tab_objects = st.tabs(list(LIGAS.values()))

for i, (code, nombre_pantalla) in enumerate(LIGAS.items()):
    with tab_objects[i]:
        # Título de Liga con Bandera
        st.markdown(f"""
        <div style="display:flex; align-items:center; color:#e5e7eb; font-size:22px; font-weight:500; margin-bottom:20px;">
            <img src="{BANDERAS[code]}" width="30" style="vertical-align:middle; margin-right:10px;">
            <span>{nombre_pantalla}</span>
        </div>
        """, unsafe_allow_html=True)

        archivo_sufijo = MAPEO_ARCHIVOS.get(nombre_pantalla)
        
        # --- MENÚ DE NAVEGACIÓN INTERNO ---
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            mostrar_fixture = st.button(f"📅 Ver Fixture {nombre_pantalla}", key=f"fix_{code}")
        
        with col_btn2:
            # Seleccionador de equipo
            df_stats = cargar_excel(f"RESUMEN_STATS_{archivo_sufijo}.xlsx")
            if df_stats is not None:
                col_equipo = 'Equipo' if 'Equipo' in df_stats.columns else 'Squad'
                lista_equipos = df_stats[col_equipo].unique().tolist()
                equipo_sel = st.selectbox("🔍 Ver Estadísticas de Equipo:", ["Seleccionar..."] + lista_equipos, key=f"sel_{code}")
            else:
                st.warning("Excel de estadísticas no encontrado.")
                equipo_sel = "Seleccionar..."

        st.divider()

        # --- LÓGICA DE VISUALIZACIÓN ---
        
        # 1. Si elige un equipo específico
        if equipo_sel != "Seleccionar...":
            st.subheader(f"📊 Estadísticas: {equipo_sel}")
            # Cargamos el excel individual del equipo desde la carpeta Ligas_Equipos
            nombre_file = equipo_sel.replace(" ", "_")
            df_individual = cargar_excel(f"Ligas_Equipos/{nombre_file}.xlsx")
            
            if df_individual is not None:
                st.dataframe(df_individual, use_container_width=True, hide_index=True)
            else:
                st.error("No se encontró el archivo individual para este equipo.")

        # 2. Si presiona el botón de Fixture (Cartelera)
        elif mostrar_fixture:
            st.subheader(f"📅 Próximos Partidos: {nombre_pantalla}")
            df_cartelera = cargar_excel(f"CARTELERA_PROXIMOS_{archivo_sufijo}.xlsx")
            
            if df_cartelera is not None:
                # Mostramos fixture limpio (sin Nonnes)
                st.dataframe(df_cartelera, use_container_width=True, hide_index=True)
            else:
                st.error("No se encontró el archivo de cartelera.")
        
        # 3. Vista por defecto (Resumen de Liga)
        else:
            if df_stats is not None:
                st.subheader("🏆 Tabla General y Rendimiento")
                st.dataframe(df_stats, use_container_width=True, hide_index=True)
