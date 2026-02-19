import streamlit as st
import pandas as pd
import numpy as np
import re
import requests

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
    'CrdY': 'AMARILLAS', 'CrdR': 'ROJAS', 'xG': 'xG'
}

# ────────────────────────────────────────────────
# FUNCIONES DE CUOTAS Y FORMATO
# ────────────────────────────────────────────────

def obtener_cuotas_api(liga_nombre):
    sport_key = MAPEO_ODDS_API.get(liga_nombre)
    if not sport_key or not API_KEY: return None
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
    params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h', 'oddsFormat': 'decimal'}
    try:
        response = requests.get(url, params=params)
        return response.json()
    except: return None

def procesar_cuotas(data):
    if not data or not isinstance(data, list): return None
    rows = []
    for match in data:
        home_team = match.get('home_team')
        away_team = match.get('away_team')
        commence_time = pd.to_datetime(match.get('commence_time')).strftime('%d/%m %H:%M')
        odds_h, odds_d, odds_a = 0.0, 0.0, 0.0
        if match.get('bookmakers'):
            bookie = next((b for b in match['bookmakers'] if b['key'].lower() == 'bet365'), match['bookmakers'][0])
            markets = bookie.get('markets', [])
            if markets:
                outcomes = markets[0].get('outcomes', [])
                for out in outcomes:
                    if out['name'] == home_team: odds_h = float(out['price'])
                    elif out['name'] == away_team: odds_a = float(out['price'])
                    else: odds_d = float(out['price'])
        rows.append({"FECHA": commence_time, "LOCAL": home_team, "VISITANTE": away_team, "1": odds_h, "X": odds_d, "2": odds_a})
    return pd.DataFrame(rows)

def badge_cuota(val, es_minimo=False):
    color_bg = "#137031" if es_minimo else "#2d3139"
    color_text = "#00ff88" if es_minimo else "#ced4da"
    return f'<div style="display: flex; justify-content: center;"><span style="background-color: {color_bg}; color: {color_text}; padding: 5px 12px; border-radius: 6px; font-weight: bold; font-size: 13px; min-width: 55px; text-align: center; border: 1px solid #4b5563;">{val:.2f}</span></div>'

# ────────────────────────────────────────────────
# ESTILOS CSS
# ────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e5e7eb; }
    .table-scroll { width: 100%; max-height: 550px; overflow: auto; border: 1px solid #374151; border-radius: 8px; margin-bottom: 20px; }
    th { position: sticky; top: 0; background-color: #1f2937 !important; color: white !important; padding: 12px; border: 1px solid #374151; text-align: center !important; }
    td { padding: 12px; border: 1px solid #374151; text-align: center !important; }
    .header-container { display: flex; align-items: center; justify-content: flex-start; gap: 15px; margin: 20px 0; padding-left: 10px; }
    .header-title { color: white !important; font-size: 2rem; font-weight: bold; margin: 0; }
    .flag-img { width: 45px; height: auto; border-radius: 4px; }
    div.stButton > button { background-color: #ff1800 !important; color: white !important; font-weight: bold !important; border-radius: 8px; height: 45px; }
</style>
""", unsafe_allow_html=True)

# Logo
st.markdown('<div style="text-align:center; margin-bottom:20px;"><img src="https://i.postimg.cc/C516P7F5/33.png" width="300"></div>', unsafe_allow_html=True)

# Lógica de Navegación
if "liga_actual" not in st.session_state: st.session_state.liga_actual = None
if "vista_activa" not in st.session_state: st.session_state.vista_activa = None

if st.button("COMPETENCIAS"):
    st.session_state.menu_abierto = True
else:
    if "menu_abierto" not in st.session_state: st.session_state.menu_abierto = False

if st.session_state.menu_abierto:
    sel = st.selectbox("Selecciona liga", ["-- Elige una --"] + LIGAS_LISTA)
    if sel != "-- Elige una --":
        st.session_state.liga_actual = sel
        st.session_state.menu_abierto = False
        st.rerun()

if st.session_state.liga_actual:
    liga = st.session_state.liga_actual
    link_bandera = BANDERAS.get(liga, "")
    st.markdown(f'<div class="header-container"><img src="{link_bandera}" class="flag-img"><h1 class="header-title">{liga}</h1></div>', unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("Clasificación"): st.session_state.vista_activa = "clas"
    if c2.button("Stats Generales"): st.session_state.vista_activa = "stats"
    if c3.button("Ver Fixture"): st.session_state.vista_activa = "fix"
    if c4.button("Picks & Cuotas"): st.session_state.vista_activa = "odds"

    st.divider()

    view = st.session_state.vista_activa
    if view == "odds":
        with st.spinner('Cargando picks...'):
            raw = obtener_cuotas_api(liga)
            df_odds = procesar_cuotas(raw)
            if df_odds is not None and not df_odds.empty:
                # Aplicar badges dinámicos
                def aplicar_badges(row):
                    cuotas = [row['1'], row['X'], row['2']]
                    min_val = min(cuotas)
                    row['1'] = badge_cuota(row['1'], row['1'] == min_val)
                    row['X'] = badge_cuota(row['X'], row['X'] == min_val)
                    row['2'] = badge_cuota(row['2'], row['2'] == min_val)
                    return row

                df_final = df_odds.apply(aplicar_badges, axis=1)
                styler = df_final.style.hide(axis="index")
                st.markdown(f'<div class="table-scroll">{styler.to_html(escape=False)}</div>', unsafe_allow_html=True)
            else:
                st.warning("Sin datos de cuotas.")
