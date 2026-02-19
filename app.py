import streamlit as st
import pandas as pd

# ────────────────────────────────────────────────
# CONFIGURACIÓN
# ────────────────────────────────────────────────
st.set_page_config(page_title="InsideBet", layout="wide")

# CONFIGURACIÓN DE GITHUB
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
# ESTILO CSS Y FUNCIONES DE COLOR
# ────────────────────────────────────────────────
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] {
        overflow: visible !important;
        height: auto !important;
    }
    .stApp { background-color: #0e1117; color: #e5e7eb; }
    .block-container { max-width: 95% !important; padding-top: 2rem !important; }
    
    .stButton > button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #1f2937;
        color: white;
        border: 1px solid #374151;
        font-weight: bold;
    }
    .stButton > button:hover {
        border-color: #3b82f6;
        color: #3b82f6;
    }
</style>
""", unsafe_allow_html=True)

def estilo_last_5(val):
    """Aplica colores a las letras W, D, L en la columna Last 5"""
    val_str = str(val).upper()
    if 'W' in val_str:
        color = '#137031' # Verde oscuro
    elif 'L' in val_str:
        color = '#821f1f' # Rojo oscuro
    elif 'D' in val_str:
        color = '#82711f' # Amarillo/Dorado
    else:
        return ''
    return f'background-color: {color}; color: white; font-weight: bold; text-align: center; border-radius: 2px;'

# ────────────────────────────────────────────────
# ENCABEZADO
# ────────────────────────────────────────────────
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
        df = pd.read_excel(url)
        return df.dropna(how='all') if not df.empty else df
    except:
        return None

# ────────────────────────────────────────────────
# INTERFAZ POR PESTAÑAS
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
        
        # --- FILA 1: BOTONES DE VISTA ---
        col1, col2, col3 = st.columns(3)
        with col1:
            btn_clasif = st.button(f"🏆 Clasificación", key=f"btn_clas_{code}")
        with col2:
            btn_stats = st.button(f"📊 Stats Generales", key=f"btn_stats_{code}")
        with col3:
            btn_fix = st.button(f"📅 Ver Fixture", key=f"btn_fix_{code}")

        # --- FILA 2: SELECTOR DE EQUIPO ---
        df_para_lista = cargar_excel(f"RESUMEN_STATS_{archivo_sufijo}.xlsx")
        equipo_sel = "Seleccionar..."
        
        if df_para_lista is not None:
            # Buscamos la columna del nombre del equipo
            col_eq_name = next((c for c in df_para_lista.columns if c in ['Equipo', 'Squad', 'Squad ']), df_para_lista.columns[0])
            lista_equipos = sorted([str(x) for x in df_para_lista[col_eq_name].unique() if str(x) != 'nan' and 'Total' not in str(x)])
            equipo_sel = st.selectbox("🔍 Analizar Equipo Individual:", ["Seleccionar..."] + lista_equipos, key=f"sel_{code}")

        st.divider()

        # --- LÓGICA DE VISUALIZACIÓN ---
        
        # A. SI SE SELECCIONA UN EQUIPO
        if equipo_sel != "Seleccionar...":
            st.subheader(f"📊 Reporte Detallado: {equipo_sel}")
            nombre_file = equipo_sel.replace(" ", "_")
            df_ind = cargar_excel(f"Ligas_Equipos/{nombre_file}.xlsx")
            if df_ind is not None:
                st.dataframe(df_ind, use_container_width=True, hide_index=True)
            else:
                st.warning(f"No se encontró el archivo específico para {equipo_sel}")

        # B. BOTÓN CLASIFICACIÓN (CON ESTILO DE COLORES)
        elif btn_clasif:
            st.subheader(f"🏆 Clasificación Oficial: {nombre_pantalla}")
            df_c = cargar_excel(f"CLASIFICACION_LIGA_{archivo_sufijo}.xlsx")
            if df_c is not None:
                # Aplicamos estilos
                styler = df_c.style
                
                # Color en Last 5
                if 'Last 5' in df_c.columns:
                    styler = styler.applymap(estilo_last_5, subset=['Last 5'])
                
                # Gradiente en Puntos (PTS)
                if 'PTS' in df_c.columns:
                    styler = styler.background_gradient(subset=['PTS'], cmap='Blues')

                st.dataframe(styler, use_container_width=True, hide_index=True, height=650)
            else:
                st.error("Error al cargar Clasificación.")

        # C. BOTÓN STATS GENERALES
        elif btn_stats:
            st.subheader(f"📊 Rendimiento de Escuadras: {nombre_pantalla}")
            if df_para_lista is not None:
                st.dataframe(df_para_lista, use_container_width=True, hide_index=True, height=650)

        # D. BOTÓN FIXTURE
        elif btn_fix:
            st.subheader(f"📅 Cartelera de Próximos Partidos: {nombre_pantalla}")
            df_f = cargar_excel(f"CARTELERA_PROXIMOS_{archivo_sufijo}.xlsx")
            if df_f is not None:
                st.dataframe(df_f, use_container_width=True, hide_index=True, height=650)

        else:
            st.info("💡 Selecciona una de las opciones superiores para visualizar los datos.")
