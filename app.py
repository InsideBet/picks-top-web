import streamlit as st
import pandas as pd
import numpy as np
import re

# ────────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ────────────────────────────────────────────────
st.set_page_config(page_title="InsideBet", layout="wide")

USER = "InsideBet" 
REPO = "picks-top-web"
BASE_URL = f"https://raw.githubusercontent.com/{USER}/{REPO}/main/datos_fbref"

LIGAS_ORDENADAS = [
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
# FUNCIONES DE PROCESAMIENTO
# ────────────────────────────────────────────────

def limpiar_nombre_equipo(nombre):
    if pd.isna(nombre): return ""
    return re.sub(r'^[a-z]{2,3}\s+', '', str(nombre))

def formatear_xg_badge(val):
    try:
        num = float(val)
        if num > 2.50: label, color = "+2.5", "#137031"
        elif num > 1.50: label, color = "+1.5", "#137031"
        else: label, color = "+0.5", "#821f1f"
        return f'<div style="display:flex;justify-content:center;"><span style="background-color:{color};color:white;padding:4px 10px;border-radius:6px;font-weight:bold;font-size:12px;min-width:45px;text-align:center;">{label}</span></div>'
    except: return val

def html_barra_posesion(valor):
    try:
        clean_val = str(valor).replace('%', '').strip()
        num = float(clean_val)
        percent = int(round(num if num > 1 else num * 100))
        percent = min(max(percent, 0), 100)
        return f'<div class="bar-container"><div class="bar-bg"><div class="bar-fill" style="width:{percent}%;"></div></div><div class="bar-text">{percent}%</div></div>'
    except: return valor

def formatear_last_5(valor):
    if pd.isna(valor): return ""
    trad = {'W': 'G', 'L': 'P', 'D': 'E'}
    letras = list(str(valor).upper().replace(" ", ""))[:5]
    html_str = '<div class="forma-container">'
    for l in letras:
        clase = "win" if l == 'W' else "loss" if l == 'L' else "draw" if l == 'D' else ""
        html_str += f'<span class="forma-box {clase}">{trad.get(l, l)}</span>'
    return html_str + '</div>'

@st.cache_data(ttl=300)
def cargar_excel(ruta_archivo, tipo="general"):
    url = f"{BASE_URL}/{ruta_archivo}"
    try:
        df = pd.read_excel(url)
        for col in ['Squad', 'Home', 'Away']:
            if col in df.columns:
                df[col] = df[col].apply(limpiar_nombre_equipo)

        if tipo == "stats":
            if len(df.columns) >= 17:
                df = df.rename(columns={df.columns[16]: 'xG'})
            df.columns = [str(c).strip() for c in df.columns]
            if 'xG' in df.columns: df['xG'] = df['xG'].apply(formatear_xg_badge)
            if 'Poss' in df.columns: df['Poss'] = df['Poss'].apply(html_barra_posesion)
            cols_ok = ['Squad', 'MP', 'Poss', 'Gls', 'Ast', 'CrdY', 'CrdR', 'xG']
            df = df[[c for c in cols_ok if c in df.columns]]

        elif tipo == "clasificacion":
            drop_c = ['Notes', 'Goalkeeper', 'Top Team Scorer', 'Attendance', 'Pts/MP', 'Pts/PJ']
            df = df.drop(columns=[c for c in drop_c if c in df.columns])
            df = df.rename(columns=TRADUCCIONES)
            cols = list(df.columns)
            if 'EQUIPO' in cols and 'PTS' in cols:
                cols.remove('EQUIPO'); cols.remove('PTS')
                df = df[['EQUIPO', 'PTS'] + cols]
            # IMPORTANTE: Aseguramos que retorne el DF procesado
            return df

        df = df.rename(columns=TRADUCCIONES)
        return df.dropna(how='all')
    except: return None

# ────────────────────────────────────────────────
# ESTILOS CSS (SOLUCIÓN SCROLL Y TABLAS)
# ────────────────────────────────────────────────
st.markdown("""
<style>
    /* Forzar scroll en el contenedor principal */
    .main { overflow: auto !important; }
    .stApp { background-color: #0e1117; color: #e5e7eb; }
    
    /* Padding inferior masivo para que el Fixture respire */
    .block-container { padding-bottom: 20rem !important; }
    
    /* Contenedor de tablas */
    .table-scroll { width: 100%; max-height: 480px; overflow: auto; border: 1px solid #374151; border-radius: 8px; margin-bottom: 40px; }
    th { position: sticky; top: 0; background-color: #1f2937 !important; color: white; padding: 12px; border: 1px solid #374151; font-size: 13px; text-align: center !important; z-index: 99; }
    td { padding: 10px; border: 1px solid #374151; font-size: 14px; text-align: center !important; white-space: nowrap; }
    
    /* Formas y Barras */
    .bar-container { display: flex; align-items: center; justify-content: flex-start; gap: 8px; width: 140px; margin: 0 auto; }
    .bar-bg { background-color: #2d3139; border-radius: 10px; flex-grow: 1; height: 7px; overflow: hidden; }
    .bar-fill { background-color: #ff1800; height: 100%; border-radius: 10px; }
    .bar-text { font-size: 12px; font-weight: bold; min-width: 32px; text-align: right; }
    .forma-container { display: flex; justify-content: center; gap: 4px; }
    .forma-box { width: 22px; height: 22px; line-height: 22px; text-align: center; border-radius: 4px; font-weight: bold; font-size: 11px; color: white; }
    .win { background-color: #137031; } .loss { background-color: #821f1f; } .draw { background-color: #82711f; }
    
    /* Botón y Selectbox */
    div.stButton > button { background-color: #ff1800 !important; color: white !important; font-weight: bold !important; width: 100%; border-radius: 8px; height: 3.5em; border: none; }
    .stSelectbox label { color: #ff1800 !important; font-weight: bold !important; }
    
    /* Titulos de sección */
    .section-title { background: #1f2937; padding: 12px; border-radius: 8px 8px 0 0; border-left: 6px solid #ff1800; font-weight: bold; margin-top: 10px; color: white; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# INTERFAZ DE USUARIO
# ────────────────────────────────────────────────
st.markdown('<div style="text-align:center; margin-bottom:20px;"><img src="https://i.postimg.cc/C516P7F5/33.png" width="300"></div>', unsafe_allow_html=True)

if "active_menu" not in st.session_state:
    st.session_state.active_menu = False

# Botón Toggle
if st.button("COMPETENCIAS"):
    st.session_state.active_menu = not st.session_state.active_menu

if st.session_state.active_menu:
    col_sel, _ = st.columns([2, 1])
    with col_sel:
        # Usamos index=0 y un placeholder
        liga = st.selectbox("¿Qué liga quieres buscar?", ["Selecciona..."] + LIGAS_ORDENADAS)

    if liga != "Selecciona...":
        sufijo = MAPEO_ARCHIVOS.get(liga)
        
        # --- CLASIFICACIÓN ---
        st.markdown('<div class="section-title">🏆 CLASIFICACIÓN</div>', unsafe_allow_html=True)
        df_c = cargar_excel(f"CLASIFICACION_LIGA_{sufijo}.xlsx", tipo="clasificacion")
        if df_c is not None:
            if 'ÚLTIMOS 5' in df_c.columns: 
                df_c['ÚLTIMOS 5'] = df_c['ÚLTIMOS 5'].apply(formatear_last_5)
            st.markdown(f'<div class="table-scroll">{df_c.style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)
        else:
            st.error(f"Error al cargar clasificación de {liga}")

        # --- STATS ---
        st.markdown('<div class="section-title">📊 STATS GENERALES</div>', unsafe_allow_html=True)
        df_s = cargar_excel(f"RESUMEN_STATS_{sufijo}.xlsx", tipo="stats")
        if df_s is not None:
            st.markdown(f'<div class="table-scroll">{df_s.style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

        # --- FIXTURE ---
        st.markdown('<div class="section-title">📅 FIXTURE / PRÓXIMOS</div>', unsafe_allow_html=True)
        df_f = cargar_excel(f"CARTELERA_PROXIMOS_{sufijo}.xlsx", tipo="fixture")
        if df_f is not None:
            st.markdown(f'<div class="table-scroll">{df_f.style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)
