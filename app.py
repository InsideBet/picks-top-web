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
    /* Fondo general de la app */
    .stApp { 
        background-color: #0e1117; 
        color: #e5e7eb; 
    }
    
    /* CONTENEDOR DE SCROLL MAESTRO (Horizontal y Vertical) */
    .table-scroll {
        width: 100%;
        max-height: 450px; /* Altura máxima para scrolleo vertical */
        overflow-x: auto !important; /* Scroll horizontal */
        overflow-y: auto !important; /* Scroll vertical */
        display: block;
        border: 1px solid #374151;
        border-radius: 8px;
    }

    /* Estilo de la barra de scroll para que sea fina y roja */
    .table-scroll::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    .table-scroll::-webkit-scrollbar-thumb {
        background: #ff1800;
        border-radius: 10px;
    }
    .table-scroll::-webkit-scrollbar-track {
        background: #1f2937;
    }

    /* Forzar que la tabla no se encoja en PC */
    .table-scroll table {
        min-width: 850px; 
        width: 100%;
    }

    /* Fijar el encabezado de la tabla para que no desaparezca al scrollear abajo */
    .table-scroll th {
        position: sticky;
        top: 0;
        z-index: 10;
        background-color: #1f2937 !important;
    }

    /* Box de información (st.info) */
    div[data-testid="stNotification"], div[role="alert"] {
        background-color: #ff1800 !important;
        border: none !important;
        border-radius: 8px !important;
    }
    
    div[data-testid="stNotificationContent"] p, 
    div[data-testid="stNotificationContent"],
    div[role="alert"] div,
    div[role="alert"] {
        color: white !important;
        font-weight: 600 !important;
    }

    div[role="alert"] svg { fill: white !important; }

    /* Contenedor Cuadraditos Forma */
    .forma-container { display: flex; justify-content: center; gap: 4px; min-width: 120px; }
    .forma-box { flex: 0 0 22px; height: 22px; line-height: 22px; text-align: center; border-radius: 4px; font-weight: bold; font-size: 11px; color: white; }
    .win { background-color: #137031; }
    .loss { background-color: #821f1f; }
    .draw { background-color: #82711f; }

    /* Estilo de Tablas HTML */
    table { border-collapse: collapse; color: #e5e7eb; }
    th { padding: 12px; border: 1px solid #374151; font-size: 13px; text-align: center !important; }
    td { padding: 10px; border: 1px solid #374151; font-size: 14px; text-align: center !important; white-space: nowrap !important; }
    tr:hover { background-color: #21262d; }

    /* Estilo para los botones */
    div.stButton > button {
        background-color: #ff1800 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        width: 100% !important;
        font-weight: bold !important;
    }
    div.stButton > button:hover {
        background-color: #cc1300 !important;
        border: 1px solid white !important;
    }
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
        if tipo == "clasificacion":
            drop_cols = ['Notes', 'Goalkeeper', 'Top Team Scorer', 'Attendance', 'Pts/MP', 'Pts/PJ']
        elif tipo == "fixture":
            drop_cols = ['Day', 'Score', 'Referee', 'Match Report', 'Notes', 'Attendance', 'Wk', 'JORNADA']
        else:
            drop_cols = []
            
        df = df.drop(columns=[c for c in drop_cols if c in df.columns])
        df = df.rename(columns=TRADUCCIONES)
        
        if tipo == "clasificacion" and 'PTS' in df.columns and 'EQUIPO' in df.columns:
            cols = list(df.columns)
            cols.insert(cols.index('EQUIPO') + 1, cols.pop(cols.index('PTS')))
            df = df[cols]
            
        return df.dropna(how='all')
    except:
        return None

# ────────────────────────────────────────────────
# INTERFAZ
# ────────────────────────────────────────────────
st.markdown('<div style="text-align:center; margin-bottom:20px;"><img src="https://i.postimg.cc/C516P7F5/33.png" width="300"></div>', unsafe_allow_html=True)

tab_objects = st.tabs(list(LIGAS.values()))

for i, (code, nombre_pantalla) in enumerate(LIGAS.items()):
    with tab_objects[i]:
        archivo_sufijo = MAPEO_ARCHIVOS.get(nombre_pantalla)
        
        if f"show_{code}" not in st.session_state:
            st.session_state[f"show_{code}"] = None

        col1, col2, col3 = st.columns(3)
        
        if col1.button(f"🏆 Clasificación", key=f"btn_clas_{code}"):
            st.session_state[f"show_{code}"] = "clas" if st.session_state[f"show_{code}"] != "clas" else None
        
        if col2.button(f"📊 Stats Generales", key=f"btn_stats_{code}"):
            st.session_state[f"show_{code}"] = "stats" if st.session_state[f"show_{code}"] != "stats" else None
            
        if col3.button(f"📅 Ver Fixture", key=f"btn_fix_{code}"):
            st.session_state[f"show_{code}"] = "fix" if st.session_state[f"show_{code}"] != "fix" else None

        st.divider()

        current_view = st.session_state[f"show_{code}"]

        if current_view == "clas":
            df_c = cargar_excel(f"CLASIFICACION_LIGA_{archivo_sufijo}.xlsx", tipo="clasificacion")
            if df_c is not None:
                col_forma = 'ÚLTIMOS 5' if 'ÚLTIMOS 5' in df_c.columns else 'Last 5'
                if col_forma in df_c.columns:
                    df_c[col_forma] = df_c[col_forma].apply(formatear_last_5)
                styler = df_c.style.hide(axis='index')
                if 'PTS' in df_c.columns:
                    styler = styler.set_properties(subset=['PTS'], **{'background-color': '#262c35', 'font-weight': 'bold'})
                
                st.markdown(f'<div class="table-scroll">{styler.to_html(escape=False)}</div>', unsafe_allow_html=True)
            else:
                st.error("Archivo no encontrado.")

        elif current_view == "stats":
            df_s = cargar_excel(f"RESUMEN_STATS_{archivo_sufijo}.xlsx")
            if df_s is not None:
                # También aplicamos el contenedor de scroll a Stats Generales
                st.markdown('<div class="table-scroll">', unsafe_allow_html=True)
                st.dataframe(df_s, use_container_width=True, hide_index=True)
                st.markdown('</div>', unsafe_allow_html=True)

        elif current_view == "fix":
            df_f = cargar_excel(f"CARTELERA_PROXIMOS_{archivo_sufijo}.xlsx", tipo="fixture")
            if df_f is not None:
                styler_f = df_f.style.hide(axis='index')
                st.markdown(f'<div class="table-scroll">{styler_f.to_html(escape=False)}</div>', unsafe_allow_html=True)
            else:
                st.error("Archivo no encontrado.")

        else:
            st.info("Selecciona una opción para ver los datos.")
