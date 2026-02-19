import streamlit as st
import pandas as pd
import numpy as np

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

TRADUCCIONES = {
    'Rk': 'POS', 'Squad': 'EQUIPO', 'MP': 'PJ', 'W': 'G', 'D': 'E', 'L': 'P',
    'GF': 'GF', 'GA': 'GC', 'GD': 'DG', 'Pts': 'PTS', 'PTS': 'PTS',
    'Last 5': 'ÚLTIMOS 5', 'Wk': 'JORNADA', 'Date': 'FECHA', 'Time': 'HORA',
    'Home': 'LOCAL', 'Away': 'VISITANTE', 'Venue': 'ESTADIO',
    'Poss': 'POSESIÓN', 'Gls': 'GOLES', 'Ast': 'ASISTENCIAS', 
    'CrdY': 'AMARILLAS', 'CrdR': 'ROJAS', 'xG': 'xG'
}

# ────────────────────────────────────────────────
# ESTILO CSS
# ────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e5e7eb; }
    
    .table-scroll {
        width: 100%;
        max-height: 450px; 
        overflow-x: auto !important;
        overflow-y: auto !important;
        display: block;
        border: 1px solid #374151;
        border-radius: 8px;
        margin-bottom: 20px;
    }

    .table-scroll::-webkit-scrollbar { width: 8px; height: 8px; }
    .table-scroll::-webkit-scrollbar-thumb { background: #ff1800; border-radius: 10px; }
    .table-scroll::-webkit-scrollbar-track { background: #1f2937; }

    .table-scroll table { min-width: 850px; width: 100%; border-collapse: collapse; }

    .table-scroll th {
        position: sticky; top: 0; z-index: 10;
        background-color: #1f2937 !important;
        color: #e5e7eb; padding: 12px; border: 1px solid #374151;
        font-size: 13px; text-align: center !important;
    }

    div[data-testid="stNotification"], div[role="alert"] {
        background-color: #ff1800 !important;
        border: none !important; border-radius: 8px !important;
    }
    
    div[data-testid="stNotificationContent"] p, div[role="alert"] div {
        color: white !important; font-weight: 600 !important;
    }
    div[role="alert"] svg { fill: white !important; }

    td { padding: 10px; border: 1px solid #374151; font-size: 14px; text-align: center !important; white-space: nowrap !important; }
    tr:hover { background-color: #21262d; }

    .forma-container { display: flex; justify-content: center; gap: 4px; min-width: 120px; }
    .forma-box { flex: 0 0 22px; height: 22px; line-height: 22px; text-align: center; border-radius: 4px; font-weight: bold; font-size: 11px; color: white; }
    .win { background-color: #137031; }
    .loss { background-color: #821f1f; }
    .draw { background-color: #82711f; }

    div.stButton > button {
        background-color: #ff1800 !important; color: white !important;
        border: none !important; border-radius: 8px !important;
        padding: 10px 20px !important; width: 100% !important; font-weight: bold !important;
    }
    div.stButton > button:hover { background-color: #cc1300 !important; border: 1px solid white !important; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# FUNCIONES DE PROCESAMIENTO
# ────────────────────────────────────────────────
def color_xg(val, min_val, max_val):
    """ Función para asignar color según el valor de xG """
    try:
        val = float(val)
        # Dividimos en tercios para semáforo
        tercio = (max_val - min_val) / 3
        if val >= min_val + 2 * tercio:
            color = "#137031" # Verde (Peligro alto)
        elif val >= min_val + tercio:
            color = "#82711f" # Amarillo (Promedio)
        else:
            color = "#821f1f" # Rojo (Bajo peligro)
        return f'background-color: {color}; color: white; font-weight: bold;'
    except:
        return ''

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
            df = df.drop(columns=[c for c in drop_cols if c in df.columns])
        elif tipo == "fixture":
            drop_cols = ['Day', 'Score', 'Referee', 'Match Report', 'Notes', 'Attendance', 'Wk', 'JORNADA']
            df = df.drop(columns=[c for c in drop_cols if c in df.columns])
        elif tipo == "stats":
            columnas_interes = ['Squad', 'MP', 'Poss', 'Gls', 'Ast', 'CrdY', 'CrdR', 'xG']
            df = df[[c for c in columnas_interes if c in df.columns]]

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
            else: st.error("Archivo no encontrado.")

        elif current_view == "stats":
            df_s = cargar_excel(f"RESUMEN_STATS_{archivo_sufijo}.xlsx", tipo="stats")
            if df_s is not None:
                # Lógica de Semáforo para xG
                if 'xG' in df_s.columns:
                    min_val = df_s['xG'].min()
                    max_val = df_s['xG'].max()
                    styler_s = df_s.style.hide(axis='index').applymap(lambda x: color_xg(x, min_val, max_val), subset=['xG'])
                else:
                    styler_s = df_s.style.hide(axis='index')
                
                st.markdown(f'<div class="table-scroll">{styler_s.to_html(escape=False)}</div>', unsafe_allow_html=True)
            else: st.error("Archivo no encontrado.")

        elif current_view == "fix":
            df_f = cargar_excel(f"CARTELERA_PROXIMOS_{archivo_sufijo}.xlsx", tipo="fixture")
            if df_f is not None:
                styler_f = df_f.style.hide(axis='index')
                st.markdown(f'<div class="table-scroll">{styler_f.to_html(escape=False)}</div>', unsafe_allow_html=True)
            else: st.error("Archivo no encontrado.")

        else:
            st.info("Selecciona una opción para ver los datos.")
