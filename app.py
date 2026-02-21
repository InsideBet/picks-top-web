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
    'CrdY': 'AMARILLAS', 'CrdR': 'ROJAS', 'xG': 'xG',
    'Player': 'JUGADOR', 'Pos': 'POS', 'Min': 'MIN', 'Sh': 'REM', 'SoT': 'PUERTA', 'Fls': 'FALT_C', 'Fld': 'FALT_R'
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

def formatear_xg_badge(val):
    try:
        num = float(val)
        color = "#137031" if num > 1.50 else "#821f1f"
        return f'<div style="display: flex; justify-content: center;"><span style="background-color: {color}; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 12px; min-width: 45px; text-align: center;">+{num:.1f}</span></div>'
    except: return val

def html_barra_posesion(valor):
    try:
        num_str = str(valor).replace('%', '').strip()
        num_clean = re.findall(r"[-+]?\d*\.\d+|\d+", num_str)[0]
        num = float(num_clean)
        percent = min(max(int(num), 0), 100)
        return f'''
        <div style="position: relative; width: 100%; background-color: #2d3139; border-radius: 4px; height: 20px; overflow: hidden; border: 1px solid #4b5563;">
            <div style="width: {percent}%; background-color: #1ed7de; height: 100%;"></div>
            <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: white; font-size: 11px; font-weight: bold; text-shadow: 1px 1px 2px black;">
                {percent}%
            </div>
        </div>
        '''
    except: return valor

def formatear_last_5(valor):
    if pd.isna(valor) or valor == "": return ""
    trad = {'W': 'G', 'L': 'P', 'D': 'E'}
    letras = list(str(valor).upper().replace(" ", ""))[:5]
    html_str = '<div style="display: flex; gap: 4px; justify-content: center;">'
    for l in letras:
        clase_color = "#137031" if l == 'W' else "#821f1f" if l == 'L' else "#82711f" if l == 'D' else "#2d3139"
        html_str += f'<span style="background-color: {clase_color}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; min-width: 20px; text-align: center;">{trad.get(l, l)}</span>'
    return html_str + '</div>'

# ────────────────────────────────────────────────
# CARGA DE DATOS
# ────────────────────────────────────────────────

@st.cache_data(ttl=300)
def cargar_excel(ruta_archivo, tipo="general"):
    if "SUPER_STATS" in ruta_archivo:
        url = f"{BASE_URL}/Estadisticas_Jugadores/{ruta_archivo}"
    else:
        url = f"{BASE_URL}/{ruta_archivo}"
    try:
        df = pd.read_excel(url)
        if tipo == "stats":
            if 'Squad' in df.columns: df['Squad'] = df['Squad'].apply(limpiar_nombre_equipo)
            if 'Poss' in df.columns: df['Poss'] = df['Poss'].apply(html_barra_posesion)
            if 'xG' in df.columns: df['xG'] = df['xG'].apply(formatear_xg_badge)
            df = df.rename(columns=TRADUCCIONES)
        elif tipo == "clasificacion":
            if 'Squad' in df.columns: df['Squad'] = df['Squad'].apply(limpiar_nombre_equipo)
            df = df.rename(columns=TRADUCCIONES)
        return df.dropna(how='all').reset_index(drop=True)
    except: return None

# ────────────────────────────────────────────────
# ESTILOS CSS
# ────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e5e7eb; }
    .table-container { width: 100%; overflow-x: auto; border: 1px solid #1ed7de44; border-radius: 8px; margin-bottom: 20px; background-color: #161b22; }
    table { width: 100%; border-collapse: collapse; }
    th { background-color: #1f2937 !important; color: #1ed7de !important; padding: 12px; text-align: center !important; }
    td { padding: 12px; border: 1px solid #374151; text-align: center !important; }
    .main-logo-container { text-align: center; padding: 20px 0; }
    .main-logo-img { width: 50%; max-width: 500px; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# APP PRINCIPAL
# ────────────────────────────────────────────────
st.markdown('<div class="main-logo-container"><img src="https://i.postimg.cc/SKPzCcyV/33.png" class="main-logo-img"></div>', unsafe_allow_html=True)

if "liga_sel" not in st.session_state: st.session_state.liga_sel = None
if "vista_activa" not in st.session_state: st.session_state.vista_activa = None
if "limit_players" not in st.session_state: st.session_state.limit_players = 10

if st.button("COMPETENCIAS", use_container_width=True):
    st.session_state.menu_op = not st.get("menu_op", False)

sel = st.selectbox("Ligas", ["Selecciona Liga"] + LIGAS_LISTA, label_visibility="collapsed")
if sel != "Selecciona Liga":
    st.session_state.liga_sel = sel
    st.session_state.vista_activa = "clas"

if st.session_state.liga_sel:
    liga = st.session_state.liga_sel
    sufijo = MAPEO_ARCHIVOS.get(liga)
    
    col_menu = st.columns(5)
    vistas = {"Clasificación": "clas", "Stats Equipos": "stats", "Análisis Jugadores": "players", "Fixture": "fix", "Odds": "odds"}
    for i, (label, key) in enumerate(vistas.items()):
        if col_menu[i].button(label, use_container_width=True):
            st.session_state.vista_activa = key
            st.session_state.limit_players = 10
            st.rerun()

    if st.session_state.vista_activa == "players":
        df_p = cargar_excel(f"SUPER_STATS_{sufijo}.xlsx", "general")
        if df_p is not None:
            # 1. Limpieza inicial de datos para evitar duplicados o errores de equipo
            df_p['Squad'] = df_p['Squad'].apply(limpiar_nombre_equipo)
            
            # 2. PANEL DE FILTROS
            f_col1, f_col2, f_col3 = st.columns([2, 2, 2])
            with f_col1:
                p_busq = st.text_input("🔍 Buscar Jugador", "").strip().lower()
                eq_f = st.selectbox("Equipo", ["Todos"] + sorted(df_p['Squad'].unique().tolist()))
            with f_col2:
                p_sel = st.multiselect("Posición", df_p['Pos'].unique(), default=df_p['Pos'].unique())
                m_min = st.number_input("Minutos mín.", 0, 5000, 90)
            with f_col3:
                st.write("**🏆 TOP PICKS (Basado en forma)**")
                top_filter = st.radio("Priorizar por:", ["Ninguno", "Ataque & Remates", "Disciplina"], horizontal=True)

            # 3. LÓGICA DE FILTRADO (SIN DUPLICAR FILAS)
            df_filtered = df_p.copy()
            
            # Filtro de búsqueda (Prioridad absoluta)
            if p_busq:
                df_filtered = df_filtered[df_filtered['Player'].str.lower().str.contains(p_busq)]
            else:
                # Si no hay búsqueda, aplicamos filtros normales
                df_filtered = df_filtered[(df_filtered['Min'] >= m_min) & (df_filtered['Pos'].isin(p_sel))]
                if eq_f != "Todos":
                    df_filtered = df_filtered[df_filtered['Squad'] == eq_f]

            # 4. APLICACIÓN DE TOP PICKS (SORTING)
            # Re-ordenamos el DataFrame según la elección del usuario
            if top_filter == "Ataque & Remates":
                # Ordenamos por Remates a Puerta y luego Goles
                df_filtered = df_filtered.sort_values(by=['SoT', 'Gls', 'Sh'], ascending=False)
            elif top_filter == "Disciplina":
                # Ordenamos por Faltas cometidas y Amarillas
                df_filtered = df_filtered.sort_values(by=['Fls', 'CrdY'], ascending=False)
            
            # 5. RENDERIZADO DE TABS
            t1, t2, t3 = st.tabs(["🎯 ATAQUE", "🛡️ DISCIPLINA", "📋 GENERAL"])
            
            with t1:
                cols_atk = ['Player', 'Squad', 'Gls', 'Ast', 'Sh', 'SoT']
                df_view = df_filtered[cols_atk].head(st.session_state.limit_players).rename(columns=TRADUCCIONES)
                st.markdown(f'<div class="table-container">{df_view.style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

            with t2:
                cols_disc = ['Player', 'Squad', 'Fls', 'Fld', 'CrdY', 'CrdR']
                df_view = df_filtered[cols_disc].head(st.session_state.limit_players).rename(columns=TRADUCCIONES)
                st.markdown(f'<div class="table-container">{df_view.style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

            with t3:
                cols_gen = ['Player', 'Squad', 'Pos', 'Age', 'Min']
                df_view = df_filtered[cols_gen].head(st.session_state.limit_players).rename(columns=TRADUCCIONES)
                st.markdown(f'<div class="table-container">{df_view.style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

            # Botón Ver Más
            if len(df_filtered) > st.session_state.limit_players:
                if st.button("Cargar más jugadores", use_container_width=True):
                    st.session_state.limit_players += 10
                    st.rerun()

        else:
            st.warning("No se pudieron cargar las estadísticas de jugadores.")

    # (El resto de vistas: clas, stats, fix se mantienen con la lógica de carga estándar)
    elif st.session_state.vista_activa == "clas":
        df_c = cargar_excel(f"CLASIFICACION_LIGA_{sufijo}.xlsx", "clasificacion")
        if df_c is not None:
            if 'ÚLTIMOS 5' in df_c.columns: df_c['ÚLTIMOS 5'] = df_c['ÚLTIMOS 5'].apply(formatear_last_5)
            st.markdown(f'<div class="table-container">{df_c.style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

st.write("---")
st.caption("InsideBet Official | scrapeo")
