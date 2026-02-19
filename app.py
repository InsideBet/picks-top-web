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
            return df

        df = df.rename(columns=TRADUCCIONES)
        return df.dropna(how='all')
    except: return None

# ────────────────────────────────────────────────
# ESTILOS CSS
# ────────────────────────────────────────────────
st.markdown("""
<style>
    /* Estilo general y Padding para permitir scroll final */
    .stApp { background-color: #0e1117; color: #e5e7eb; }
    .main .block-container { padding-bottom: 300px; } 
    
    .table-scroll { width: 100%; max-height: 480px; overflow: auto; border: 1px solid #374151; border-radius: 8px; margin-bottom: 30px; }
    th { position: sticky; top: 0; background-color: #1f2937 !important; color: white; padding: 12px; border: 1px solid #374151; font-size: 13px; text-align: center !important; z-index: 2; }
    td { padding: 10px; border: 1px solid #374151; font-size: 14px; text-align: center !important; white-space: nowrap; }
    
    .bar-container { display: flex; align-items: center; justify-content: flex-start; gap: 8px; width: 140px; margin: 0 auto; }
    .bar-bg { background-color: #2d3139; border-radius: 10px; flex-grow: 1; height: 7px; overflow: hidden; }
    .bar-fill { background-color: #ff1800; height: 100%; border-radius: 10px; }
    .bar-text { font-size: 12px; font-weight: bold; min-width: 32px; text-align: right; }
    
    .forma-container { display: flex; justify-content: center; gap: 4px; }
    .forma-box { width: 22px; height: 22px; line-height: 22px; text-align: center; border-radius: 4px; font-weight: bold; font-size: 11px; color: white; }
    .win { background-color: #137031; } .loss { background-color: #821f1f; } .draw { background-color: #82711f; }
    
    /* Botón COMPETENCIAS */
    div.stButton > button { background-color: #ff1800 !important; color: white !important; font-weight: bold !important; width: 100%; border-radius: 8px; border: none !important; height: 3.5em; font-size: 16px; transition: 0.3s; }
    div.stButton > button:hover { transform: scale(1.01); background-color: #e61600 !important; }
    
    .stSelectbox label { color: #ff1800 !important; font-weight: bold !important; font-size: 16px !important; }
    
    .section-title { background: #1f2937; padding: 12px; border-radius: 8px 8px 0 0; border-left: 6px solid #ff1800; font-weight: bold; margin-top: 10px; color: white; font-size: 15px; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# INTERFAZ DE USUARIO
# ────────────────────────────────────────────────
st.markdown('<div style="text-align:center; margin-bottom:20px;"><img src="https://i.postimg.cc/C516P7F5/33.png" width="300"></div>', unsafe_allow_html=True)

if "mostrar_todo" not in st.session_state:
    st.session_state.mostrar_todo = False

# Botón Principal
if st.button("COMPETENCIAS"):
    st.session_state.mostrar_todo = not st.session_state.mostrar_todo

if st.session_state.mostrar_todo:
    col_sel, _ = st.columns([2, 1])
    with col_sel:
        liga_seleccionada = st.selectbox("¿Qué liga quieres buscar?", ["Selecciona una competencia..."] + LIGAS_ORDENADAS)

    if liga_seleccionada != "Selecciona una competencia...":
        archivo_sufijo = MAPEO_ARCHIVOS.get(liga_seleccionada)
        
        # 1. CLASIFICACIÓN
        st.markdown('<div class="section-title">🏆 CLASIFICACIÓN</div>', unsafe_allow_html=True)
        df_clas = cargar_excel(f"CLASIFICACION_LIGA_{archivo_sufijo}.xlsx", tipo="clasificacion")
        if df_clas is not None:
            if 'ÚLTIMOS 5' in df_clas.columns: 
                df_clas['ÚLTIMOS 5'] = df_clas['ÚLTIMOS 5'].apply(formatear_last_5)
            st.markdown(f'<div class="table-scroll">{df_clas.style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)
        else:
            st.info(f"No hay datos de clasificación disponibles para {liga_seleccionada}.")

        # 2. STATS GENERALES
        st.markdown('<div class="section-title">📊 STATS GENERALES</div>', unsafe_allow_html=True)
        df_stats = cargar_excel(f"RESUMEN_STATS_{archivo_sufijo}.xlsx", tipo="stats")
        if df_stats is not None:
            st.markdown(f'<div class="table-scroll">{df_stats.style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

        # 3. FIXTURE
        st.markdown('<div class="section-title">📅 FIXTURE / PRÓXIMOS</div>', unsafe_allow_html=True)
        df_fix = cargar_excel(f"CARTELERA_PROXIMOS_{archivo_sufijo}.xlsx", tipo="fixture")
        if df_fix is not None:
            st.markdown(f'<div class="table-scroll">{df_fix.style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)
