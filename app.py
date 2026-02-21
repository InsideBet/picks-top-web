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
    'Player': 'JUGADOR', 'Pos': 'POS', 'Min': 'MIN', 'Sh': 'REMATES', 'SoT': 'REMATES A PUERTA', 'Fls': 'FALTAS COMETIDAS', 'Fld': 'FALTAS RECIBIDAS'
}

MAPEO_POSICIONES = {
    'FW': 'DEL', 'MF': 'MED', 'DF': 'DEF', 'GK': 'POR',
    'FW,MF': 'DEL/MED', 'MF,FW': 'MED/DEL', 'DF,MF': 'DEF/MED', 'MF,DF': 'MED/DEF'
}

# ────────────────────────────────────────────────
# FUNCIONES DE FORMATO
# ────────────────────────────────────────────────

def limpiar_nombre_equipo(nombre):
    if pd.isna(nombre) or str(nombre).lower() == 'nan': return ""
    txt = str(nombre).strip()
    txt = re.sub(r'^[a-z]{2,3}\s+', '', txt, flags=re.IGNORECASE)
    txt = re.sub(r'\s+[a-z]{2,3}$', '', txt, flags=re.IGNORECASE)
    return txt.strip()

def get_badge_fiabilidad(mins, score):
    """Genera el badge de fiabilidad según tu imagen de referencia"""
    try:
        m = float(mins)
        if m < 300: return "BAJA (POCA MUESTRA) ⚠️", "#00bcd4"
        if m >= 450: return "ALTA 🔥", "#ff4b4b"
        return "MEDIA 📈", "#00bcd4"
    except: return "N/A", "#4b5563"

def grafico_picos_forma(valor, alineacion="left"):
    if pd.isna(valor) or valor == "": return ""
    letras = list(str(valor).upper().replace(" ", ""))[:5]
    mapeo_y = {'W': 4, 'D': 11, 'L': 18}
    colores = {'W': '#137031', 'D': '#b59410', 'L': '#821f1f'}
    puntos = [f"{10+(i*25)},{mapeo_y.get(l, 11)}" for i, l in enumerate(letras)]
    circles = [f'<circle cx="{10+(i*25)}" cy="{mapeo_y.get(l, 11)}" r="3" fill="{colores.get(l, "#4b5563")}" />' for i, l in enumerate(letras)]
    return f'<svg width="130" height="22"><path d="M {" L ".join(puntos)}" fill="none" stroke="#1ed7de" stroke-width="1.2" opacity="0.4" />{"".join(circles)}</svg>'

# ────────────────────────────────────────────────
# CARGA DE DATOS
# ────────────────────────────────────────────────

@st.cache_data(ttl=300)
def cargar_excel(ruta_archivo, tipo="general"):
    # Respetamos tu ruta original de carpetas
    url = f"{BASE_URL}/Estadisticas_Jugadores/{ruta_archivo}" if "SUPER_STATS" in ruta_archivo else f"{BASE_URL}/{ruta_archivo}"
    try:
        df = pd.read_excel(url)
        if 'Squad' in df.columns: df['Squad'] = df['Squad'].apply(limpiar_nombre_equipo)
        if tipo == "clasificacion":
            df = df.rename(columns=TRADUCCIONES)
        return df.dropna(how='all').reset_index(drop=True)
    except: return None

# ────────────────────────────────────────────────
# ESTILOS CSS (Fiel a Screenshot_20.png)
# ────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e5e7eb; }
    .pick-card { 
        background: #161b22; border: 1px solid #1ed7de33; border-radius: 10px; 
        padding: 20px; margin-bottom: 15px; height: 180px;
    }
    .badge-f { font-size: 10px; font-weight: bold; padding: 2px 8px; border-radius: 4px; }
    .stat-box { text-align: center; }
    .stat-val { color: #1ed7de; font-size: 18px; font-weight: bold; }
    .stat-label { font-size: 9px; color: #9ca3af; }
    .table-container { width: 100%; overflow-x: auto; border: 1px solid #1ed7de44; border-radius: 8px; background-color: #161b22; }
    th { background-color: #1f2937 !important; color: #1ed7de !important; padding: 10px; }
    td { border: 1px solid #374151; padding: 10px; text-align: center !important; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# ESTRUCTURA PRINCIPAL
# ────────────────────────────────────────────────
st.markdown('<center><img src="https://i.postimg.cc/SKPzCcyV/33.png" width="400"></center>', unsafe_allow_html=True)

if "liga_sel" not in st.session_state: st.session_state.liga_sel = None
if "vista_activa" not in st.session_state: st.session_state.vista_activa = "clas"
if "num_jugadores_mostrados" not in st.session_state: st.session_state.num_jugadores_mostrados = 10

if st.button("COMPETENCIAS", use_container_width=True):
    st.session_state.menu_op = not st.session_state.get('menu_op', False)

if st.session_state.get('menu_op', False):
    sel = st.selectbox("Ligas", ["Selecciona Liga"] + LIGAS_LISTA, label_visibility="collapsed")
    if sel != "Selecciona Liga":
        st.session_state.liga_sel = sel
        st.session_state.menu_op = False
        st.rerun()

if st.session_state.liga_sel:
    liga = st.session_state.liga_sel
    sufijo = MAPEO_ARCHIVOS[liga]
    st.markdown(f'### <img src="{BANDERAS.get(liga)}" width="30"> {liga}')
    
    # Botones de navegación
    cols = st.columns(4)
    if cols[0].button("Clasificación", use_container_width=True): st.session_state.vista_activa = "clas"
    if cols[1].button("Stats Equipos", use_container_width=True): st.session_state.vista_activa = "stats"
    if cols[2].button("Análisis Jugadores", use_container_width=True): 
        st.session_state.vista_activa = "players"
        st.session_state.num_jugadores_mostrados = 10
    if cols[3].button("Picks & Cuotas", use_container_width=True): st.session_state.vista_activa = "odds"

    view = st.session_state.vista_activa

    if view == "players":
        # SECCIÓN DE TOP PICKS (Screenshot_20.png)
        st.markdown("#### 🔥 TOP PICKS DE ÉLITE (Basado en Promedios/90min)")
        df_picks = cargar_excel("picks_finales_fiables.xlsx") # Asumiendo este archivo para los cuadros
        if df_picks is not None:
            df_l = df_picks[df_picks['Liga'] == sufijo].head(6)
            p_cols = st.columns(3)
            for i, (idx, row) in enumerate(df_l.iterrows()):
                label, color = get_badge_fiabilidad(row.get('Minutos', 500), row.get('Score_Pick', 0))
                with p_cols[i % 3]:
                    st.markdown(f"""
                    <div class="pick-card">
                        <span class="badge-f" style="color:{color}; border:1px solid {color};">{label}</span>
                        <div style="font-size:16px; font-weight:bold; margin-top:10px;">{row['Jugador']}</div>
                        <div style="font-size:12px; color:#9ca3af; margin-bottom:15px;">{row['Equipo']}</div>
                        <div style="display:flex; justify-content:space-between; border-top:1px solid #374151; padding-top:10px;">
                            <div class="stat-box"><div class="stat-val">{row['Faltas_90']}</div><div class="stat-label">FALTAS/90</div></div>
                            <div class="stat-box"><div class="stat-val">{row['Tiros_90']}</div><div class="stat-label">TIROS/90</div></div>
                            <div class="stat-box"><div class="stat-val" style="color:#b59410;">{row['Score_Pick']}</div><div class="stat-label">SCORE</div></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # TABLAS DE JUGADORES (Tu lógica de pestañas y Ver más)
        df_p = cargar_excel(f"SUPER_STATS_{sufijo}.xlsx")
        if df_p is not None:
            if 'Pos' in df_p.columns: df_p['Pos'] = df_p['Pos'].replace(MAPEO_POSICIONES)
            t1, t2 = st.tabs(["🎯 ATAQUE & REMATES", "🛡️ DISCIPLINA"])
            
            with t1:
                df_t1 = df_p[['Player', 'Squad', 'Gls', 'Ast', 'Sh', 'SoT']].sort_values(by='Gls', ascending=False)
                st.markdown(f'<div class="table-container">{df_t1.head(st.session_state.num_jugadores_mostrados).rename(columns=TRADUCCIONES).to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)
                if st.button("Ver más jugadores (Ataque)"):
                    st.session_state.num_jugadores_mostrados += 10
                    st.rerun()
            
            with t2:
                df_t2 = df_p[['Player', 'Squad', 'Fls', 'Fld', 'CrdY', 'CrdR']].sort_values(by='Fls', ascending=False)
                st.markdown(f'<div class="table-container">{df_t2.head(st.session_state.num_jugadores_mostrados).rename(columns=TRADUCCIONES).to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)
                if st.button("Ver más jugadores (Disciplina)"):
                    st.session_state.num_jugadores_mostrados += 10
                    st.rerun()

    elif view == "clas":
        df = cargar_excel(f"CLASIFICACION_LIGA_{sufijo}.xlsx", "clasificacion")
        if df is not None:
            st.markdown(f'<div class="table-container">{df.to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)

st.write("---")
st.caption("InsideBet Official | scrapeo")
