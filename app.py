import streamlit as st
import pandas as pd

# ────────────────────────────────────────────────
# CONFIGURACIÓN
# ────────────────────────────────────────────────
st.set_page_config(page_title="InsideBet", layout="wide")

# SUSTITUYE CON TU USUARIO REAL DE GITHUB
USER = "InsideBet" 
REPO = "picks-top-web"
BASE_URL = f"https://raw.githubusercontent.com/{USER}/{REPO}/main/datos_fbref"

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
# ESTILO, SCROLL GLOBAL Y AJUSTES VISUALES
# ────────────────────────────────────────────────
st.markdown("""
<style>
    /* 1. Forzar que la página tenga scroll natural */
    html, body , [data-testid="stDecoration"] {
        overflow: visible !important;
    }

    .main {
        overflow: visible !important;
    }

    /* 2. Ajustar el contenedor para que no corte el contenido */
    .block-container {
        max-width: 95% !important;
        padding-top: 2rem !important;
        padding-bottom: 10rem !important; /* Espacio extra al final */
        overflow: visible !important;
    }

    /* 3. Evitar que las tablas "bloqueen" el scroll del mouse */
    .stDataFrame, [data-testid="stTable"] {
        margin-bottom: 20px;
    }

    /* 4. Estilo general de colores */
    .stApp { 
        background-color: #0e1117; 
        color: #e5e7eb; 
    }
</style>
""", unsafe_allow_html=True)

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
@st.cache_data(ttl=300)
def cargar_excel(ruta_archivo):
    url = f"{BASE_URL}/{ruta_archivo}"
    try:
        # Cargamos el dataframe
        df = pd.read_excel(url)
        
        # Limpieza de filas vacías (None) en el fixture
        # Buscamos columnas comunes de equipos
        for col in ['Local', 'Home', 'Squad', 'Equipo']:
            if col in df.columns:
                df = df.dropna(subset=[col])
                break
        return df
    except Exception as e:
        # Imprime el error en la consola de Streamlit para debuggear si hace falta
        return None

# ────────────────────────────────────────────────
# INTERFAZ
# ────────────────────────────────────────────────
tab_objects = st.tabs(list(LIGAS.values()))

for i, (code, nombre_pantalla) in enumerate(LIGAS.items()):
    with tab_objects[i]:
        st.markdown(f"""
        <div style="display:flex; align-items:center; color:#e5e7eb; font-size:22px; font-weight:500; margin-bottom:20px;">
            <img src="{BANDERAS[code]}" width="30" style="vertical-align:middle; margin-right:10px;">
            <span>{nombre_pantalla}</span>
        </div>
        """, unsafe_allow_html=True)

        archivo_sufijo = MAPEO_ARCHIVOS.get(nombre_pantalla)
        
        # Intentamos cargar el resumen de stats primero para llenar el selector
        df_stats = cargar_excel(f"RESUMEN_STATS_{archivo_sufijo}.xlsx")

        # Layout de botones superiores
        col_btn1, col_btn2 = st.columns([1, 2])
        
        with col_btn1:
            mostrar_fixture = st.button(f"📅 Ver Fixture {nombre_pantalla}", key=f"btn_fix_{code}")
        
        with col_btn2:
            if df_stats is not None:
                col_eq_name = next((c for c in df_stats.columns if c in ['Equipo', 'Squad', 'Unnamed: 1']), df_stats.columns[1])
                lista_equipos = sorted([str(x) for x in df_stats[col_eq_name].unique() if str(x) != 'nan'])
                equipo_sel = st.selectbox("🔍 Analizar Equipo:", ["Seleccionar..."] + lista_equipos, key=f"sel_{code}")
            else:
                st.error("⚠️ No se pudo conectar con el Excel de estadísticas en GitHub.")
                equipo_sel = "Seleccionar..."

        st.divider()

        # ÁREA DE RESULTADOS
        if equipo_sel != "Seleccionar...":
            st.subheader(f"📊 Reporte Detallado: {equipo_sel}")
            # Carpeta Ligas_Equipos tiene los archivos individuales
            nombre_file = equipo_sel.replace(" ", "_")
            df_ind = cargar_excel(f"Ligas_Equipos/{nombre_file}.xlsx")
            if df_ind is not None:
                st.dataframe(df_ind, use_container_width=True, hide_index=True)
            else:
                st.warning(f"No se encontró el archivo específico para {equipo_sel}")

        elif mostrar_fixture:
            st.subheader(f"📅 Calendario Próximo: {nombre_pantalla}")
            df_fix = cargar_excel(f"CARTELERA_PROXIMOS_{archivo_sufijo}.xlsx")
            if df_fix is not None:
                st.dataframe(df_fix, use_container_width=True, hide_index=True, height=800)
            else:
                st.error("No se pudo cargar la cartelera.")

        else:
            # Vista por defecto: Tabla de la liga
            if df_stats is not None:
                st.subheader("🏆 Clasificación y Stats Generales")
                st.dataframe(df_stats, use_container_width=True, hide_index=True, height=600)
