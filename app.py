import streamlit as st
import pandas as pd
import numpy as np
import re
import requests
import os

# ────────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ────────────────────────────────────────────────
st.set_page_config(page_title="InsideBet", layout="wide")

# Mantengo tus secretos y constantes exactas
try:
    API_KEY = st.secrets["odds_api_key"]
except:
    API_KEY = None

USER = "InsideBet" 
REPO = "picks-top-web"
BASE_URL = f"https://raw.githubusercontent.com/{USER}/{REPO}/main/datos_fbref"

LIGAS_LISTA = ["Champions League", "Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1", "Primeira Liga", "Eredivisie"]

MAPEO_ARCHIVOS = {
    "Premier League": "Premier_League", "La Liga": "La_Liga", "Serie A": "Serie_A",
    "Bundesliga": "Bundesliga", "Ligue 1": "Ligue_1", "Primeira Liga": "Primeira_Liga",
    "Eredivisie": "Eredivisie", "Champions League": "Champions_League"
}

MAPEO_ODDS_API = {
    "Premier League": "soccer_epl", "La Liga": "soccer_spain_la_liga", "Serie A": "soccer_italy_serie_a",
    "Bundesliga": "soccer_germany_bundesliga", "Ligue 1": "soccer_france_ligue_1",
    "Primeira Liga": "soccer_portugal_primeira_liga", "Eredivisie": "soccer_netherlands_eredivisie",
    "Champions League": "soccer_uefa_champions_league"
}

BANDERAS = {
    "Champions League": "https://i.postimg.cc/XYHkj56d/7.png", "Premier League": "https://i.postimg.cc/v1L6Fk5T/1.png",
    "La Liga": "https://i.postimg.cc/sByvcmbd/8.png", "Serie A": "https://i.postimg.cc/vDmxkPTQ/4.png",
    "Bundesliga": "https://i.postimg.cc/vg0gDnqQ/3.png", "Ligue 1": "https://i.postimg.cc/7GHJx9NR/2.png",
    "Primeira Liga": "https://i.postimg.cc/QH99xHcb/5.png", "Eredivisie": "https://i.postimg.cc/dLb77wB8/6.png"
}

TRADUCCIONES = {
    'Rk': 'POS', 'Squad': 'EQUIPO', 'MP': 'PJ', 'W': 'G', 'D': 'E', 'L': 'P',
    'GF': 'GF', 'GA': 'GC', 'GD': 'DG', 'Pts': 'PTS', 'PTS': 'PTS',
    'Last 5': 'ÚLTIMOS 5', 'Wk': 'JORNADA', 'Date': 'FECHA', 'Time': 'HORA',
    'Home': 'LOCAL', 'Away': 'VISITANTE', 'Venue': 'ESTADIO',
    'Poss': 'POSESIÓN', 'Gls': 'GOLES', 'Ast': 'ASISTENCIAS', 
    'CrdY': '🟨', 'CrdR': '🟥', 'xG': 'xG',
    'Player': 'JUGADOR', 'Pos': 'POS', 'Min': 'MIN', 'Sh': 'REMATES', 'SoT': 'REMATES A PUERTA', 'Fls': 'FALTAS COMETIDS', 'Fld': 'FALTAS RECIBIDAS'
}

MAPEO_POSICIONES = {
    'FW': 'DEL', 'MF': 'MED', 'DF': 'DEF', 'GK': 'POR',
    'FW,MF': 'DEL/MED', 'MF,FW': 'MED/DEL', 'DF,MF': 'DEF/MED', 'MF,DF': 'MED/DEF'
}

# ────────────────────────────────────────────────
# FUNCIONES DE FORMATO (Solo añadidas, no modifican lógica anterior)
# ────────────────────────────────────────────────

def limpiar_nombre_equipo(nombre):
    if pd.isna(nombre) or str(nombre).lower() == 'nan': return ""
    txt = str(nombre).strip()
    txt = re.sub(r'^[a-z]{2,3}\s+', '', txt, flags=re.IGNORECASE)
    txt = re.sub(r'\s+[a-z]{2,3}$', '', txt, flags=re.IGNORECASE)
    return txt.strip()

def generar_sparkline_score(score):
    """Mini tendencia SVG sin afectar datos"""
    val = float(score) if score else 0
    p = [val * 0.9, val * 0.95, val]
    mx = max(p) if max(p) > 0 else 1
    n = [(v/mx)*18 for v in p]
    return f'<svg width="40" height="18"><polyline points="0,{18-n[0]} 20,{18-n[1]} 40,{18-n[2]}" fill="none" stroke="#1ed7de" stroke-width="2" /></svg>'

def color_fiabilidad(mins, score):
    if mins < 300: return "#821f1f", "BAJA ⚠️"
    if mins >= 450: return "#137031", "ALTA 🔥"
    return "#b59410", "MEDIA 📈"

def grafico_picos_forma(valor):
    if pd.isna(valor) or valor == "": return ""
    letras = list(str(valor).upper().replace(" ", ""))[:5]
    mapeo_y = {'W': 4, 'D': 11, 'L': 18}
    pts = [f"{10+(i*25)},{mapeo_y.get(l, 11)}" for i, l in enumerate(letras)]
    circles = [f'<circle cx="{10+(i*25)}" cy="{mapeo_y.get(l, 11)}" r="3" fill="{"#137031" if l=="W" else "#b59410" if l=="D" else "#821f1f"}" />' for i, l in enumerate(letras)]
    return f'<svg width="130" height="22"><path d="M {" L ".join(pts)}" fill="none" stroke="#1ed7de" stroke-width="1" opacity="0.3"/>{"".join(circles)}</svg>'

# ────────────────────────────────────────────────
# CARGA DE DATOS (Mantenida como tú la tenías)
# ────────────────────────────────────────────────

@st.cache_data(ttl=300)
def cargar_excel(ruta_archivo, tipo="general"):
    if "SUPER_STATS" in ruta_archivo:
        url = f"{BASE_URL}/Estadisticas_Jugadores/{ruta_archivo}"
    else:
        url = f"{BASE_URL}/{ruta_archivo}"
    
    try:
        df = pd.read_excel(url)
        if 'Squad' in df.columns: df['Squad'] = df['Squad'].apply(limpiar_nombre_equipo)
        
        if tipo == "stats":
            if 'Poss' in df.columns:
                df['Poss_num'] = df['Poss'].str.replace('%','').astype(float)
            if len(df.columns) >= 17:
                df['xG_val'] = df.iloc[:, 16]
            df = df.rename(columns=TRADUCCIONES)
        elif tipo == "clasificacion":
            df = df.rename(columns=TRADUCCIONES)
        return df
    except:
        return None

# ────────────────────────────────────────────────
# INTERFAZ Y RENDERIZADO
# ────────────────────────────────────────────────

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e5e7eb; }
    .table-container { width: 100%; overflow-x: auto; border: 1px solid #1ed7de44; border-radius: 8px; background-color: #161b22; }
    th { background-color: #1f2937 !important; color: #1ed7de !important; text-align: center !important; }
    td { text-align: center !important; border: 1px solid #374151 !important; }
    .pick-card { background: #1f2937; border: 1px solid #1ed7de44; border-radius: 10px; padding: 15px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<center><img src="https://i.postimg.cc/SKPzCcyV/33.png" width="400"></center>', unsafe_allow_html=True)

# Lógica de navegación original
if "liga_sel" not in st.session_state: st.session_state.liga_sel = None
if "vista_activa" not in st.session_state: st.session_state.vista_activa = "clas"

if st.button("COMPETENCIAS", use_container_width=True):
    st.session_state.menu_op = not st.session_state.get('menu_op', False)

if st.session_state.get('menu_op', False):
    sel = st.selectbox("Selecciona", LIGAS_LISTA)
    st.session_state.liga_sel = sel
    st.session_state.menu_op = False
    st.rerun()

if st.session_state.liga_sel:
    liga = st.session_state.liga_sel
    sufijo = MAPEO_ARCHIVOS[liga]
    
    st.markdown(f"## <img src='{BANDERAS[liga]}' width='30'> {liga}")
    
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("Clasificación", use_container_width=True): st.session_state.vista_activa = "clas"
    if c2.button("Stats Equipos", use_container_width=True): st.session_state.vista_activa = "stats"
    if c3.button("Análisis Jugadores", use_container_width=True): st.session_state.vista_activa = "players"
    if c4.button("Fixture", use_container_width=True): st.session_state.vista_activa = "fix"

    if st.session_state.vista_activa == "players":
        # Bloque de Picks Top (Solo si existe el archivo)
        df_top = cargar_excel("picks_finales_fiables.xlsx")
        if df_top is not None:
            df_liga = df_top[df_top['Liga'] == sufijo].head(6)
            cols = st.columns(3)
            for i, (idx, row) in enumerate(df_liga.iterrows()):
                col_f, lab_f = color_fiabilidad(row['Minutos'], row['Score_Pick'])
                with cols[i%3]:
                    st.markdown(f"""
                    <div class="pick-card">
                        <div style="display:flex; justify-content:space-between;">
                            <span style="color:{col_f}; font-weight:bold; font-size:10px;">{lab_f}</span>
                            {generar_sparkline_score(row['Score_Pick'])}
                        </div>
                        <h4 style="margin:5px 0; color:white;">{row['Jugador']}</h4>
                        <div style="font-size:12px; color:#1ed7de;">{row['Equipo']}</div>
                        <div style="display:flex; justify-content:space-between; margin-top:10px; border-top:1px solid #4b5563; padding-top:5px;">
                            <small>Faltas: <b>{row['Faltas_90']}</b></small>
                            <small>Tiros: <b>{row['Tiros_90']}</b></small>
                            <small>Score: <b style="color:#b59410;">{row['Score_Pick']}</b></small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # Tabla de jugadores completa
        df_p = cargar_excel(f"SUPER_STATS_{sufijo}.xlsx")
        if df_p is not None:
            st.dataframe(df_p.rename(columns=TRADUCCIONES), use_container_width=True, hide_index=True)

    elif st.session_state.vista_activa == "clas":
        df = cargar_excel(f"CLASIFICACION_LIGA_{sufijo}.xlsx", "clasificacion")
        if df is not None:
            if 'ÚLTIMOS 5' in df.columns:
                df['ÚLTIMOS 5'] = df['ÚLTIMOS 5'].apply(grafico_picos_forma)
            st.markdown(f'<div class="table-container">{df.to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)

    elif st.session_state.vista_activa == "stats":
        df = cargar_excel(f"RESUMEN_STATS_{sufijo}.xlsx", "stats")
        if df is not None:
            st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown("<br><center><small>InsideBet 2026</small></center>", unsafe_allow_html=True)
