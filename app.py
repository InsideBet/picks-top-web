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
    "PL": "Premier League", "PD": "La Liga", "SA": "Serie A",
    "BL1": "Bundesliga", "FL1": "Ligue 1", "PPL": "Primeira Liga",
    "DED": "Eredivisie", "CL": "Champions League"
}

MAPEO_ARCHIVOS = {
    "Premier League": "Premier_League", "La Liga": "La_Liga", "Serie A": "Serie_A",
    "Bundesliga": "Bundesliga", "Ligue 1": "Ligue_1", "Primeira Liga": "Primeira_Liga",
    "Eredivisie": "Eredivisie", "Champions League": "Champions_League"
}

BANDERAS = {
    "PL": "https://i.postimg.cc/7PcwYbk1/1.png", "PD": "https://i.postimg.cc/75d5mMQ2/8.png",
    "SA": "https://i.postimg.cc/mzxTFmpm/4.png", "BL1": "https://i.postimg.cc/5X09cYFn/3.png",
    "FL1": "https://i.postimg.cc/jnbqBMz2/2.png", "PPL": "https://i.postimg.cc/ZBr4S61R/5.png",
    "DED": "https://i.postimg.cc/tnkbwpqv/6.png", "CL": "https://i.postimg.cc/zb1V1DNy/7.png"
}

# Diccionario Maestro de Traducción de Cabeceras
TRADUCCIONES = {
    'Rk': 'POS', 'Squad': 'EQUIPO', 'MP': 'PJ', 'W': 'G', 'D': 'E', 'L': 'P',
    'GF': 'GF', 'GA': 'GC', 'GD': 'DG', 'Pts': 'PTS', 'PTS': 'PTS',
    'Last 5': 'ÚLTIMOS 5', 'Wk': 'JORNADA', 'Date': 'FECHA', 'Time': 'HORA',
    'Home': 'LOCAL', 'Away': 'VISITANTE', 'Venue': 'ESTADIO'
}

# ────────────────────────────────────────────────
# ESTILO CSS
# ────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e5e7eb; }
    
    /* Contenedor Cuadraditos Forma */
    .forma-container {
        display: flex;
        justify-content: center;
        gap: 4px;
        min-width: 120px;
        white-space: nowrap;
    }
    .forma-box {
        flex: 0 0 22px;
        height: 22px;
        line-height: 22px;
        text-align: center;
        border-radius: 4px;
        font-weight: bold;
        font-size: 11px;
        color: white;
    }
    .win { background-color: #137031; }
    .loss { background-color: #821f1f; }
    .draw { background-color: #82711f; }

    /* Estilo de Tablas HTML */
    table { width: 100%; border-collapse: collapse; color: #e5e7eb; }
    th { background-color: #1f2937; padding: 12px; border: 1px solid #374151; font-size: 13px; text-align: center !important; }
    td { padding: 10px; border: 1px solid #374151; font-size: 14px; text-align: center !important; }
    tr:hover { background-color: #21262d; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# FUNCIONES DE PROCESAMIENTO
# ────────────────────────────────────────────────
def formatear_last_5(valor):
    if pd.isna(valor): return ""
    trad = {'W': 'G', 'L': 'P', 'D': 'E'}
    letras = list(str(valor).upper().replace(" ", ""))[:5]
    html_str = '<div class="forma-container">'
    for l in letras:
        clase = "win" if l == 'W' else "loss" if l == 'L' else "draw" if l == 'D' else ""
        html_str += f'<span class="forma-box {clase}">{trad.get(l, l)}</span>'
    html_str += '</div>'
    return html_str

@st.cache_data(ttl=300)
def cargar_excel(ruta_archivo, tipo="general"):
    url = f"{BASE_URL}/{ruta_archivo}"
    try:
        df = pd.read_excel(url)
        
        # Filtro de columnas según sección
        if tipo == "clasificacion":
            drop_cols = ['Notes', 'Goalkeeper', 'Top Team Scorer', 'Attendance', 'Pts/MP', 'Pts/PJ']
        elif tipo == "fixture":
            drop_cols = ['Day', 'Score', 'Referee', 'Match Report', 'Notes', 'Attendance']
        else:
            drop_cols = []
            
        df = df.drop(columns=[c for c in drop_cols if c in df.columns])
        df = df.rename(columns=TRADUCCIONES)
        return df.dropna(how='all')
    except:
        return None

# ────────────────────────────────────────────────
# INTERFAZ
# ────────────────────────────────────────────────
st.markdown('<div style="text-align:center; margin-bottom:20px;"><img src="https://i.postimg.cc/SNkwbQjM/33.png" width="300"></div>', unsafe_allow_html=True)

tab_objects = st.tabs(list(LIGAS.values()))

for i, (code, nombre_pantalla) in enumerate(LIGAS.items()):
    with tab_objects[i]:
        archivo_sufijo = MAPEO_ARCHIVOS.get(nombre_pantalla)
        
        col1, col2, col3 = st.columns(3)
        with col1: btn_clasif = st.button(f"🏆 Clasificación", key=f"btn_clas_{code}")
        with col2: btn_stats = st.button(f"📊 Stats Generales", key=f"btn_stats_{code}")
        with col3: btn_fix = st.button(f"📅 Ver Fixture", key=f"btn_fix_{code}")

        st.divider()

        # --- LÓGICA CLASIFICACIÓN ---
        if btn_clasif:
            df_c = cargar_excel(f"CLASIFICACION_LIGA_{archivo_sufijo}.xlsx", tipo="clasificacion")
            if df_c is not None:
                # Formatear Últimos 5
                col_forma = 'ÚLTIMOS 5' if 'ÚLTIMOS 5' in df_c.columns else 'Last 5'
                if col_forma in df_c.columns:
                    df_c[col_forma] = df_c[col_forma].apply(formatear_last_5)
                
                # Styler: Ocultar índice y color sólido en PTS
                styler = df_c.style.hide(axis='index')
                if 'PTS' in df_c.columns:
                    styler = styler.set_properties(subset=['PTS'], **{'background-color': '#262c35', 'font-weight': 'bold'})
                
                st.write(styler.to_html(escape=False), unsafe_allow_html=True)
            else:
                st.error("Archivo no encontrado.")

        # --- LÓGICA STATS GENERALES ---
        elif btn_stats:
            df_s = cargar_excel(f"RESUMEN_STATS_{archivo_sufijo}.xlsx")
            if df_s is not None:
                st.dataframe(df_s, use_container_width=True, hide_index=True)

        # --- LÓGICA FIXTURE ---
        elif btn_fix:
            df_f = cargar_excel(f"CARTELERA_PROXIMOS_{archivo_sufijo}.xlsx", tipo="fixture")
            if df_f is not None:
                # Ocultar índice y renderizar
                styler_f = df_f.style.hide(axis='index')
                st.write(styler_f.to_html(escape=False), unsafe_allow_html=True)
            else:
                st.error("Archivo no encontrado.")

        else:
            st.info("Selecciona una opción para ver los datos.")
