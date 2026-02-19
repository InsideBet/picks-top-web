import streamlit as st
import pandas as pd
import numpy as np

# ────────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
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
    "Bundesliga": "Bundesliga", "Ligue_1": "Ligue_1", "Primeira Liga": "Primeira_Liga",
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
# FUNCIONES DE PROCESAMIENTO
# ────────────────────────────────────────────────

def color_xg_fijo(val):
    """Aplica verde si es >= 1.50, rojo si es menor."""
    try:
        num = float(val)
        color = "#137031" if num >= 1.50 else "#821f1f"
        return f'background-color: {color}; color: white; font-weight: bold;'
    except: return ''

def html_barra_posesion(valor):
    """Genera el componente visual de la barra de posesión."""
    try:
        clean_val = str(valor).replace('%', '').strip()
        num = float(clean_val)
        # Ajuste por si el valor viene como 0.57 o 57
        percent = int(round(num if num > 1 else num * 100))
        percent = min(max(percent, 0), 100)
        return f'''
        <div class="bar-container">
            <div class="bar-bg"><div class="bar-fill" style="width: {percent}%;"></div></div>
            <div class="bar-text">{percent}%</div>
        </div>
        '''
    except: return valor

def formatear_last_5(valor):
    """Cajitas de colores para la clasificación."""
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
        
        if tipo == "stats":
            # APUNTAR A COLUMNA Q (Índice 16): 
            # Es la columna donde FBRef suele poner el xG en el resumen
            if len(df.columns) >= 17:
                col_q_original = df.columns[16]
                df = df.rename(columns={col_q_original: 'xG'})
            
            # Limpiar espacios en nombres de columnas
            df.columns = [str(c).strip() for c in df.columns]
            
            # Seleccionamos columnas de interés
            cols_ok = ['Squad', 'MP', 'Poss', 'Gls', 'Ast', 'CrdY', 'CrdR', 'xG']
            df = df[[c for c in cols_ok if c in df.columns]]
            
            # Aplicar barra a Posesión
            if 'Poss' in df.columns:
                df['Poss'] = df['Poss'].apply(html_barra_posesion)

        elif tipo == "clasificacion":
            drop_c = ['Notes', 'Goalkeeper', 'Top Team Scorer', 'Attendance', 'Pts/MP', 'Pts/PJ']
            df = df.drop(columns=[c for c in drop_c if c in df.columns])
            
        elif tipo == "fixture":
            drop_f = ['Day', 'Score', 'Referee', 'Match Report', 'Notes', 'Attendance', 'Wk']
            df = df.drop(columns=[c for c in drop_f if c in df.columns])

        df = df.rename(columns=TRADUCCIONES)
        return df.dropna(how='all')
    except: return None

# ────────────────────────────────────────────────
# ESTILOS CSS
# ────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e5e7eb; }
    
    /* Scroll y Contenedor de Tabla */
    .table-scroll { 
        width: 100%; 
        max-height: 450px; 
        overflow: auto; 
        border: 1px solid #374151; 
        border-radius: 8px; 
        margin-bottom: 20px; 
    }
    .table-scroll::-webkit-scrollbar { width: 8px; height: 8px; }
    .table-scroll::-webkit-scrollbar-thumb { background: #ff1800; border-radius: 10px; }
    
    .table-scroll table { min-width: 850px; width: 100%; border-collapse: collapse; }
    th { 
        position: sticky; top: 0; 
        background-color: #1f2937 !important; 
        color: white; padding: 12px; 
        border: 1px solid #374151; font-size: 13px; 
        text-align: center !important; 
    }
    td { padding: 10px; border: 1px solid #374151; font-size: 14px; text-align: center !important; white-space: nowrap; }

    /* Barra de Posesión (Solicitada por el usuario) */
    .bar-container { display: flex; align-items: center; justify-content: flex-start; gap: 8px; width: 140px; margin: 0 auto; }
    .bar-bg { background-color: #2d3139; border-radius: 10px; flex-grow: 1; height: 7px; overflow: hidden; }
    .bar-fill { background-color: #ff4b4b; height: 100%; border-radius: 10px; }
    .bar-text { font-size: 12px; font-weight: bold; min-width: 32px; text-align: right; }

    /* Cajitas de Últimos 5 */
    .forma-container { display: flex; justify-content: center; gap: 4px; }
    .forma-box { width: 22px; height: 22px; line-height: 22px; text-align: center; border-radius: 4px; font-weight: bold; font-size: 11px; color: white; }
    .win { background-color: #137031; } .loss { background-color: #821f1f; } .draw { background-color: #82711f; }

    /* Botones Rojos */
    div.stButton > button { 
        background-color: #ff1800 !important; 
        color: white !important; 
        font-weight: bold !important; 
        width: 100%; 
        border-radius: 8px; 
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# LOGO E INTERFAZ
# ────────────────────────────────────────────────
st.markdown('<div style="text-align:center; margin-bottom:20px;"><img src="https://i.postimg.cc/C516P7F5/33.png" width="300"></div>', unsafe_allow_html=True)

tab_objects = st.tabs(list(LIGAS.values()))

for i, (code, nombre_pantalla) in enumerate(LIGAS.items()):
    with tab_objects[i]:
        archivo_sufijo = MAPEO_ARCHIVOS.get(nombre_pantalla)
        if f"show_{code}" not in st.session_state: st.session_state[f"show_{code}"] = None

        c1, c2, c3 = st.columns(3)
        if c1.button(f"🏆 Clasificación", key=f"c_{code}"): st.session_state[f"show_{code}"] = "clas"
        if c2.button(f"📊 Stats Generales", key=f"s_{code}"): st.session_state[f"show_{code}"] = "stats"
        if c3.button(f"📅 Ver Fixture", key=f"f_{code}"): st.session_state[f"show_{code}"] = "fix"

        st.divider()
        view = st.session_state[f"show_{code}"]

        if view == "stats":
            df = cargar_excel(f"RESUMEN_STATS_{archivo_sufijo}.xlsx", tipo="stats")
            if df is not None:
                styler = df.style.hide(axis='index')
                if 'xG' in df.columns:
                    df['xG'] = pd.to_numeric(df['xG'], errors='coerce')
                    styler = styler.applymap(color_xg_fijo, subset=['xG'])
                st.markdown(f'<div class="table-scroll">{styler.to_html(escape=False)}</div>', unsafe_allow_html=True)
            else: st.error("No se encontró el archivo de Stats.")

        elif view == "clas":
            df = cargar_excel(f"CLASIFICACION_LIGA_{archivo_sufijo}.xlsx", tipo="clasificacion")
            if df is not None:
                if 'ÚLTIMOS 5' in df.columns: df['ÚLTIMOS 5'] = df['ÚLTIMOS 5'].apply(formatear_last_5)
                st.markdown(f'<div class="table-scroll">{df.style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

        elif view == "fix":
            df = cargar_excel(f"CARTELERA_PROXIMOS_{archivo_sufijo}.xlsx", tipo="fixture")
            if df is not None:
                st.markdown(f'<div class="table-scroll">{df.style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)
