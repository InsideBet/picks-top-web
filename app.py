import streamlit as st
import pandas as pd
import numpy as np
import re
import requests

# 1. CONFIGURACIÓN BÁSICA (Sin trucos raros de CSS iniciales)
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

# 2. FUNCIONES DE FORMATO
def limpiar_nombre_equipo(nombre):
    if pd.isna(nombre): return nombre
    return re.sub(r'^[a-z]+\s+', '', str(nombre))

def formatear_xg_badge(val):
    try:
        num = float(val)
        color = "#137031" if num > 1.50 else "#821f1f"
        return f'<div style="display: flex; justify-content: center;"><span style="background-color: {color}; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 12px; min-width: 45px; text-align: center;">+{num:.1f}</span></div>'
    except: return val

def html_barra_posesion(valor):
    try:
        num = float(str(valor).replace('%', '').strip())
        percent = min(max(int(num), 0), 100)
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
    return html_str + '</div>'

@st.cache_data(ttl=300)
def cargar_excel(ruta_archivo, tipo="general"):
    url = f"{BASE_URL}/{ruta_archivo}"
    try:
        df = pd.read_excel(url)
        col_equipo = 'Squad' if 'Squad' in df.columns else 'EQUIPO'
        if col_equipo in df.columns:
            df[col_equipo] = df[col_equipo].apply(limpiar_nombre_equipo)
        if tipo == "stats":
            if len(df.columns) >= 17: df = df.rename(columns={df.columns[16]: 'xG'})
            if 'xG' in df.columns: df['xG'] = df['xG'].apply(formatear_xg_badge)
            if 'Poss' in df.columns: df['Poss'] = df['Poss'].apply(html_barra_posesion)
            cols_ok = ['Squad', 'MP', 'Poss', 'Gls', 'Ast', 'CrdY', 'CrdR', 'xG']
            df = df[[c for c in cols_ok if c in df.columns]]
            df = df.rename(columns=TRADUCCIONES)
        elif tipo == "clasificacion":
            drop_c = ['Notes', 'Goalkeeper', 'Top Team Scorer', 'Attendance', 'Pts/MP', 'Pts/PJ']
            df = df.drop(columns=[c for c in drop_c if c in df.columns]).rename(columns=TRADUCCIONES)
            cols = list(df.columns)
            if 'EQUIPO' in cols and 'PTS' in cols:
                cols.remove('PTS'); idx = cols.index('EQUIPO'); cols.insert(idx + 1, 'PTS'); df = df[cols]
        elif tipo == "fixture":
            df = df.drop(columns=[c for c in ['Day', 'Score', 'Referee', 'Match Report', 'Notes', 'Attendance', 'Wk'] if c in df.columns]).rename(columns=TRADUCCIONES)
        return df.dropna(how='all')
    except: return None

# 3. CUOTAS
def obtener_cuotas_api(liga_nombre):
    sport_key = MAPEO_ODDS_API.get(liga_nombre)
    if not sport_key or not API_KEY: return None
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
    params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h', 'oddsFormat': 'decimal'}
    try:
        res = requests.get(url, params=params); return res.json()
    except: return None

def badge_cuota(val, es_minimo=False):
    color_bg = "#137031" if es_minimo else "#2d3139"
    color_text = "#00ff88" if es_minimo else "#ced4da"
    return f'<div style="display: flex; justify-content: center;"><span style="background-color: {color_bg}; color: {color_text}; padding: 5px 12px; border-radius: 6px; font-weight: bold; font-size: 13px; min-width: 55px; text-align: center; border: 1px solid #4b5563;">{val:.2f}</span></div>'

def procesar_cuotas(data):
    if not data or not isinstance(data, list): return None
    rows = []
    for match in data:
        home, away = match.get('home_team'), match.get('away_team')
        commence = pd.to_datetime(match.get('commence_time')).strftime('%d/%m %H:%M')
        h, d, a = 0.0, 0.0, 0.0
        if match.get('bookmakers'):
            bk = next((b for b in match['bookmakers'] if b['key'].lower() == 'bet365'), match['bookmakers'][0])
            outcomes = bk['markets'][0]['outcomes']
            for o in outcomes:
                if o['name'] == home: h = float(o['price'])
                elif o['name'] == away: a = float(o['price'])
                else: d = float(o['price'])
        rows.append({"FECHA": commence, "LOCAL": home, "VISITANTE": away, "1": h, "X": d, "2": a})
    return pd.DataFrame(rows)

# 4. CSS MINIMALISTA (ESTE NO BLOQUEA NADA)
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e5e7eb; }
    .table-container { width: 100%; overflow-x: auto; border: 1px solid #374151; border-radius: 8px; margin-bottom: 20px; }
    th { background-color: #1f2937 !important; color: white !important; padding: 12px; border: 1px solid #374151; text-align: center !important; }
    td { padding: 12px; border: 1px solid #374151; text-align: center !important; }
    .header-container { display: flex; align-items: center; gap: 15px; margin: 15px 0; }
    .header-title { color: white !important; font-size: 1.8rem; font-weight: bold; margin: 0; }
    .flag-img { width: 40px; border-radius: 4px; }
    .bar-container { display: flex; align-items: center; gap: 8px; width: 130px; margin: 0 auto; }
    .bar-bg { background-color: #2d3139; border-radius: 10px; flex-grow: 1; height: 7px; overflow: hidden; }
    .bar-fill { background-color: #ff4b4b; height: 100%; }
    .forma-container { display: flex; justify-content: center; gap: 4px; }
    .forma-box { width: 22px; height: 22px; line-height: 22px; text-align: center; border-radius: 4px; font-weight: bold; font-size: 11px; }
    .win { background-color: #137031; color: white; } .loss { background-color: #821f1f; color: white; } .draw { background-color: #82711f; color: white; }
    div.stButton > button { background-color: #ff1800 !important; color: white !important; font-weight: bold !important; border-radius: 8px; height: 45px; width: 100%; }
</style>
""", unsafe_allow_html=True)

# 5. CONTENIDO
st.markdown('<div style="text-align:center; margin-bottom:20px;"><img src="https://i.postimg.cc/C516P7F5/33.png" width="250"></div>', unsafe_allow_html=True)

if "liga_sel" not in st.session_state: st.session_state.liga_sel = None
if "vista_activa" not in st.session_state: st.session_state.vista_activa = None
if "menu_op" not in st.session_state: st.session_state.menu_op = False

if st.button("COMPETENCIAS"):
    st.session_state.menu_op = not st.session_state.menu_op

if st.session_state.menu_op:
    sel = st.selectbox("Ligas", ["-- Selecciona --"] + LIGAS_LISTA, label_visibility="collapsed")
    if sel != "-- Selecciona --":
        st.session_state.liga_sel = sel; st.session_state.menu_op = False; st.session_state.vista_activa = None; st.rerun()

if st.session_state.liga_sel:
    liga = st.session_state.liga_sel
    st.markdown(f'<div class="header-container"><img src="{BANDERAS.get(liga, "")}" class="flag-img"><h1 class="header-title">{liga}</h1></div>', unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("Clasificación"): st.session_state.vista_activa = "clas" if st.session_state.vista_activa != "clas" else None
    if c2.button("Stats Generales"): st.session_state.vista_activa = "stats" if st.session_state.vista_activa != "stats" else None
    if c3.button("Ver Fixture"): st.session_state.vista_activa = "fix" if st.session_state.vista_activa != "fix" else None
    if c4.button("Picks & Cuotas"): st.session_state.vista_activa = "odds" if st.session_state.vista_activa != "odds" else None

    st.divider()

    view = st.session_state.vista_activa
    if view:
        if view == "odds":
            with st.spinner('Scrapeo de cuotas...'):
                raw = obtener_cuotas_api(liga); df_odds = procesar_cuotas(raw)
                if df_odds is not None and not df_odds.empty:
                    def aplicar_b(row):
                        m = min(row['1'], row['X'], row['2'])
                        row['1'], row['X'], row['2'] = badge_cuota(row['1'], row['1']==m), badge_cuota(row['X'], row['X']==m), badge_cuota(row['2'], row['2']==m)
                        return row
                    html = df_odds.apply(aplicar_b, axis=1).style.hide(axis="index").to_html(escape=False)
                    st.markdown(f'<div class="table-container">{html}</div>', unsafe_allow_html=True)
        else:
            sufijo = MAPEO_ARCHIVOS.get(liga)
            archivo, tipo = (f"CLASIFICACION_LIGA_{sufijo}.xlsx", "clasificacion") if view=="clas" else (f"RESUMEN_STATS_{sufijo}.xlsx", "stats") if view=="stats" else (f"CARTELERA_PROXIMOS_{sufijo}.xlsx", "fixture")
            df = cargar_excel(archivo, tipo=tipo)
            if df is not None:
                if 'ÚLTIMOS 5' in df.columns: df['ÚLTIMOS 5'] = df['ÚLTIMOS 5'].apply(formatear_last_5)
                styler = df.style.hide(axis="index")
                if 'PTS' in df.columns: styler = styler.set_properties(subset=['PTS'], **{'background-color': '#262730', 'font-weight': 'bold'})
                st.markdown(f'<div class="table-container">{styler.to_html(escape=False)}</div>', unsafe_allow_html=True)

# 6. ANCLAJE DE SEGURIDAD (Esto fuerza a Brave a reconocer que hay contenido abajo)
st.write("---")
st.caption("InsideBet - Datos actualizados")
