import streamlit as st
import pandas as pd
import numpy as np
import re
import requests

# ────────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ────────────────────────────────────────────────
st.set_page_config(page_title="InsideBet", layout="wide")

# Acceso a API Key desde Secrets
try:
    API_KEY = st.secrets["odds_api_key"]
except:
    API_KEY = None

USER = "InsideBet" 
REPO = "picks-top-web"
BASE_URL = f"https://raw.githubusercontent.com/{USER}/{REPO}/main/datos_fbref"

LIGAS_LISTA = [
    "Champions League", "Premier League", "La Liga", "Serie A",
    "Bundesliga", "Ligue 1", "Primeira Liga", "Eredivisie"
]

MAPEO_ARCHIVOS = {
    "Premier League": "Premier_League", "La Liga": "La_Liga", "Serie A": "Serie_A",
    "Bundesliga": "Bundesliga", "Ligue 1": "Ligue_1", "Primeira Liga": "Primeira_Liga",
    "Eredivisie": "Eredivisie", "Champions League": "Champions_League"
}

MAPEO_ODDS_API = {
    "Premier League": "soccer_epl",
    "La Liga": "soccer_spain_la_liga",
    "Serie A": "soccer_italy_serie_a",
    "Bundesliga": "soccer_germany_bundesliga",
    "Ligue 1": "soccer_france_ligue_1",
    "Primeira Liga": "soccer_portugal_primeira_liga",
    "Eredivisie": "soccer_netherlands_eredivisie",
    "Champions League": "soccer_uefa_champions_league"
}

BANDERAS = {
    "Champions League": "https://i.postimg.cc/XYHkj56d/7.png",
    "Premier League": "https://i.postimg.cc/v1L6Fk5T/1.png",
    "La Liga": "https://i.postimg.cc/sByvcmbd/8.png",
    "Serie A": "https://i.postimg.cc/vDmxkPTQ/4.png",
    "Bundesliga": "https://i.postimg.cc/vg0gDnqQ/3.png",
    "Ligue 1": "https://i.postimg.cc/7GHJx9NR/2.png",
    "Primeira Liga": "https://i.postimg.cc/QH99xHcb/5.png",
    "Eredivisie": "https://i.postimg.cc/dLb77wB8/6.png"
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
# FUNCIONES DE PROCESAMIENTO (DEFINIDAS ANTES DEL USO)
# ────────────────────────────────────────────────

def limpiar_nombre_equipo(nombre):
    if pd.isna(nombre): return nombre
    return re.sub(r'^[a-z]+\s+', '', str(nombre))

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
        col_equipo = 'Squad' if 'Squad' in df.columns else 'EQUIPO'
        if col_equipo in df.columns:
            df[col_equipo] = df[col_equipo].apply(limpiar_nombre_equipo)

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
                cols.remove('PTS'); idx = cols.index('EQUIPO')
                cols.insert(idx + 1, 'PTS'); df = df[cols]
        elif tipo == "fixture":
            drop_f = ['Day', 'Score', 'Referee', 'Match Report', 'Notes', 'Attendance', 'Wk']
            df = df.drop(columns=[c for c in drop_f if c in df.columns])
            df = df.rename(columns=TRADUCCIONES)
        return df.dropna(how='all')
    except: return None

# ────────────────────────────────────────────────
# FUNCIONES DE CUOTAS
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
        
        odds_h, odds_d, odds_a = "-", "-", "-"
        if match.get('bookmakers'):
            # Buscar Bet365, si no existe, usar la primera disponible
            bookie = next((b for b in match['bookmakers'] if b['key'].lower() == 'bet365'), match['bookmakers'][0])
            markets = bookie.get('markets', [])
            if markets:
                outcomes = markets[0].get('outcomes', [])
                for out in outcomes:
                    if out['name'] == home_team: odds_h = out['price']
                    elif out['name'] == away_team: odds_a = out['price']
                    else: odds_d = out['price']
        
        rows.append({"FECHA": commence_time, "LOCAL": home_team, "VISITANTE": away_team, "1": odds_h, "X": odds_d, "2": odds_a})
    return pd.DataFrame(rows)

# ────────────────────────────────────────────────
# ESTILOS CSS
# ────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e5e7eb; }
    .table-scroll { width: 100%; max-height: 550px; overflow: auto; border: 1px solid #374151; border-radius: 8px; margin-bottom: 20px; }
    th { position: sticky; top: 0; background-color: #1f2937 !important; color: white !important; padding: 12px; border: 1px solid #374151; text-align: center !important; }
    td { padding: 10px; border: 1px solid #374151; text-align: center !important; white-space: nowrap; }
    
    .header-container { display: flex; align-items: center; justify-content: flex-start; gap: 15px; margin: 20px 0; padding-left: 10px; }
    .header-title { color: white !important; font-size: 2rem; font-weight: bold; margin: 0; }
    .flag-img { width: 45px; height: auto; border-radius: 4px; }
    
    .bar-container { display: flex; align-items: center; justify-content: flex-start; gap: 8px; width: 140px; margin: 0 auto; }
    .bar-bg { background-color: #2d3139; border-radius: 10px; flex-grow: 1; height: 7px; overflow: hidden; }
    .bar-fill { background-color: #ff4b4b; height: 100%; border-radius: 10px; }
    .bar-text { font-size: 12px; font-weight: bold; min-width: 32px; text-align: right; }
    
    .forma-container { display: flex; justify-content: center; gap: 4px; }
    .forma-box { width: 22px; height: 22px; line-height: 22px; text-align: center; border-radius: 4px; font-weight: bold; font-size: 11px; color: white; }
    .win { background-color: #137031; } .loss { background-color: #821f1f; } .draw { background-color: #82711f; }
    
    div.stButton > button { background-color: #ff1800 !important; color: white !important; font-weight: bold !important; border-radius: 8px; height: 45px; }
</style>
""", unsafe_allow_html=True)

# Logo
st.markdown('<div style="text-align:center; margin-bottom:20px;"><img src="https://i.postimg.cc/C516P7F5/33.png" width="300"></div>', unsafe_allow_html=True)

# 1. LÓGICA DE COMPETENCIAS
if "menu_abierto" not in st.session_state: st.session_state.menu_abierto = False
if "liga_actual" not in st.session_state: st.session_state.liga_actual = None
if "vista_activa" not in st.session_state: st.session_state.vista_activa = None

if st.button("COMPETENCIAS"):
    st.session_state.menu_abierto = not st.session_state.menu_abierto

if st.session_state.menu_abierto:
    seleccion = st.selectbox("Selecciona una competencia", ["Selecciona una competencia"] + LIGAS_LISTA, label_visibility="collapsed")
    if seleccion != "Selecciona una competencia":
        st.session_state.liga_actual = seleccion
        st.session_state.menu_abierto = False
        st.session_state.vista_activa = None
        st.rerun()

# 2. CONTENIDO PRINCIPAL
if st.session_state.liga_actual:
    liga = st.session_state.liga_actual
    archivo_sufijo = MAPEO_ARCHIVOS.get(liga)
    link_bandera = BANDERAS.get(liga, "")
    
    st.markdown(f'<div class="header-container"><img src="{link_bandera}" class="flag-img"><h1 class="header-title">{liga}</h1></div>', unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    def manejar_click(v): st.session_state.vista_activa = v

    if c1.button("Clasificación"): manejar_click("clas")
    if c2.button("Stats Generales"): manejar_click("stats")
    if c3.button("Ver Fixture"): manejar_click("fix")
    if c4.button("Picks & Cuotas"): manejar_click("odds")

    st.divider()

    # 3. RENDERIZADO
    view = st.session_state.vista_activa
    if view:
        if view == "odds":
            with st.spinner('Actualizando picks y cuotas...'):
                datos_raw = obtener_cuotas_api(liga)
                df_odds = procesar_cuotas(datos_raw)
                if df_odds is not None and not df_odds.empty:
                    styler = df_odds.style.hide(axis="index").set_properties(**{'color': '#ff1800', 'font-weight': 'bold'}, subset=['1', 'X', '2'])
                    st.markdown(f'<div class="table-scroll">{styler.to_html(escape=False)}</div>', unsafe_allow_html=True)
                else:
                    st.warning("No hay cuotas disponibles para esta liga en este momento.")
        else:
            tipo_carga = "stats" if view == "stats" else "clasificacion" if view == "clas" else "fixture"
            nombre_archivo = f"RESUMEN_STATS_{archivo_sufijo}.xlsx" if view == "stats" else \
                             f"CLASIFICACION_LIGA_{archivo_sufijo}.xlsx" if view == "clas" else \
                             f"CARTELERA_PROXIMOS_{archivo_sufijo}.xlsx"
            
            df = cargar_excel(nombre_archivo, tipo=tipo_carga)
            if df is not None:
                if view == "clas" and 'ÚLTIMOS 5' in df.columns:
                    df['ÚLTIMOS 5'] = df['ÚLTIMOS 5'].apply(formatear_last_5)
                styler = df.style.hide(axis="index")
                if 'PTS' in df.columns:
                    styler = styler.set_properties(subset=['PTS'], **{'background-color': '#262730', 'font-weight': 'bold'})
                st.markdown(f'<div class="table-scroll">{styler.to_html(escape=False)}</div>', unsafe_allow_html=True)
