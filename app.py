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

# Lista de ligas con Champions al principio
LIGAS_LISTA = [
    "Champions League", "Premier League", "La Liga", "Serie A",
    "Bundesliga", "Ligue 1", "Primeira Liga", "Eredivisie"
]

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
# FUNCIONES DE PROCESAMIENTO VISUAL
# ────────────────────────────────────────────────

def formatear_xg_badge(val):
    try:
        num = float(val)
        if num > 2.50: label, color = "+2.5", "#137031"
        elif num > 1.50: label, color = "+1.5", "#137031"
        else: label, color = "+0.5", "#821f1f"
        return f'<div style="display: flex; justify-content: center;"><span style="background-color: {color}; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 12px; min-width: 45px; text-align: center; display: inline-block;">{label}</span></div>'
    except: return val

def html_barra_posesion(valor):
    try:
        clean_val = str(valor).replace('%', '').strip()
        num = float(clean_val)
        percent = int(round(num if num > 1 else num * 100))
        percent = min(max(percent, 0), 100)
        return f'<div class="bar-container"><div class="bar-bg"><div class="bar-fill" style="width: {percent}%;"></div></div><div class="bar-text">{percent}%</div></div>'
    except: return valor

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
        if tipo == "stats":
            if len(df.columns) >= 17:
                col_q = df.columns[16]
                df = df.rename(columns={col_q: 'xG'})
            df.columns = [str(c).strip() for c in df.columns]
            if 'xG' in df.columns: df['xG'] = df['xG'].apply(formatear_xg_badge)
            if 'Poss' in df.columns: df['Poss'] = df['Poss'].apply(html_barra_posesion)
            cols_ok = ['Squad', 'MP', 'Poss', 'Gls', 'Ast', 'CrdY', 'CrdR', 'xG']
            df = df[[c for c in cols_ok if c in df.columns]]
            df = df.rename(columns=TRADUCCIONES)

        elif tipo == "clasificacion":
            drop_c = ['Notes', 'Goalkeeper', 'Top Team Scorer', 'Attendance', 'Pts/MP', 'Pts/PJ']
            df = df.drop(columns=[c for c in drop_c if c in df.columns])
            df = df.rename(columns=TRADUCCIONES)
            cols = list(df.columns)
            if 'EQUIPO' in cols and 'PTS' in cols:
                cols.remove('PTS')
                idx = cols.index('EQUIPO')
                cols.insert(idx + 1, 'PTS')
                df = df[cols]
            
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
    .table-scroll { width: 100%; max-height: 550px; overflow: auto; border: 1px solid #374151; border-radius: 8px; margin-bottom: 20px; }
    .table-scroll::-webkit-scrollbar { width: 8px; height: 8px; }
    .table-scroll::-webkit-scrollbar-thumb { background: #ff1800; border-radius: 10px; }
    th { position: sticky; top: 0; background-color: #1f2937 !important; color: white; padding: 12px; border: 1px solid #374151; font-size: 13px; text-align: center !important; }
    td { padding: 10px; border: 1px solid #374151; font-size: 14px; text-align: center !important; white-space: nowrap; }
    .bar-container { display: flex; align-items: center; justify-content: flex-start; gap: 8px; width: 140px; margin: 0 auto; }
    .bar-bg { background-color: #2d3139; border-radius: 10px; flex-grow: 1; height: 7px; overflow: hidden; }
    .bar-fill { background-color: #ff4b4b; height: 100%; border-radius: 10px; }
    .bar-text { font-size: 12px; font-weight: bold; min-width: 32px; text-align: right; }
    .forma-container { display: flex; justify-content: center; gap: 4px; }
    .forma-box { width: 22px; height: 22px; line-height: 22px; text-align: center; border-radius: 4px; font-weight: bold; font-size: 11px; color: white; }
    .win { background-color: #137031; } .loss { background-color: #821f1f; } .draw { background-color: #82711f; }
    div.stButton > button { background-color: #ff1800 !important; color: white !important; font-weight: bold !important; width: 100%; border-radius: 8px; border: none !important; margin-bottom: 5px; height: 45px; }
</style>
""", unsafe_allow_html=True)

# Logo
st.markdown('<div style="text-align:center; margin-bottom:20px;"><img src="https://i.postimg.cc/C516P7F5/33.png" width="300"></div>', unsafe_allow_html=True)

# 1. SELECTOR DE COMPETENCIAS CON PLACEHOLDER
opciones_con_placeholder = ["Selecciona una competencia"] + LIGAS_LISTA
liga_seleccionada = st.selectbox("COMPETENCIAS", opciones_con_placeholder, index=0)

# Inicializar estados
if "vista_activa" not in st.session_state: st.session_state.vista_activa = None
if "liga_previa" not in st.session_state: st.session_state.liga_previa = liga_seleccionada

# Si se elige el placeholder o cambia la liga, no mostrar tablas
if liga_seleccionada == "Selecciona una competencia":
    st.info("Selecciona una liga para comenzar el scrapeo de datos.")
    st.stop()

if st.session_state.liga_previa != liga_seleccionada:
    st.session_state.vista_activa = None
    st.session_state.liga_previa = liga_seleccionada

# 2. BOTONES DE ACCIÓN CON ICONOS DINÁMICOS
archivo_sufijo = MAPEO_ARCHIVOS.get(liga_seleccionada)
st.write(f"### {liga_seleccionada}")
c1, c2, c3 = st.columns(3)

def toggle_view(nueva_vista):
    if st.session_state.vista_activa == nueva_vista:
        st.session_state.vista_activa = None
    else:
        st.session_state.vista_activa = nueva_vista

# Iconos dinámicos (▼ si está abierto, ▲ o normal si está cerrado)
icon_clas = "▼" if st.session_state.vista_activa == "clas" else "🏆"
icon_stats = "▼" if st.session_state.vista_activa == "stats" else "📊"
icon_fix = "▼" if st.session_state.vista_activa == "fix" else "📅"

if c1.button(f"{icon_clas} Clasificación"): toggle_view("clas")
if c2.button(f"{icon_stats} Stats Generales"): toggle_view("stats")
if c3.button(f"{icon_fix} Ver Fixture"): toggle_view("fix")

st.divider()

# 3. RENDERIZADO
view = st.session_state.vista_activa
if view == "stats":
    df = cargar_excel(f"RESUMEN_STATS_{archivo_sufijo}.xlsx", tipo="stats")
    if df is not None:
        st.markdown(f'<div class="table-scroll">{df.style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

elif view == "clas":
    df = cargar_excel(f"CLASIFICACION_LIGA_{archivo_sufijo}.xlsx", tipo="clasificacion")
    if df is not None:
        if 'ÚLTIMOS 5' in df.columns: df['ÚLTIMOS 5'] = df['ÚLTIMOS 5'].apply(formatear_last_5)
        st.markdown(f'<div class="table-scroll">{df.style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

elif view == "fix":
    df = cargar_excel(f"CARTELERA_PROXIMOS_{archivo_sufijo}.xlsx", tipo="fixture")
    if df is not None:
        st.markdown(f'<div class="table-scroll">{df.style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)
