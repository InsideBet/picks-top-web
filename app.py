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
        num = float(str(valor).replace('%', '').strip())
        percent = min(max(int(num), 0), 100)
        return f'<div style="width: 100%; background: #2d3139; border-radius: 10px; height: 12px; position: relative;"><div style="width: {percent}%; background: #1ed7de; height: 100%; border-radius: 10px;"></div></div>'
    except: return valor

def formatear_last_5(valor):
    if pd.isna(valor): return ""
    trad = {'W': 'G', 'L': 'P', 'D': 'E'}
    letras = list(str(valor).upper().replace(" ", ""))[:5]
    html_str = '<div style="display: flex; gap: 5px; justify-content: center;">'
    for l in letras:
        bg = "#137031" if l == 'W' else "#821f1f" if l == 'L' else "#82711f" if l == 'D' else "#2d3139"
        html_str += f'<span style="background-color: {bg}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; min-width: 22px; display: inline-block;">{trad.get(l, l)}</span>'
    return html_str + '</div>'

@st.cache_data(ttl=300)
def cargar_excel(ruta_archivo, tipo="general"):
    url = f"{BASE_URL}/{ruta_archivo}"
    try:
        df = pd.read_excel(url)
        if tipo == "stats":
            if 'Squad' in df.columns: df['Squad'] = df['Squad'].apply(limpiar_nombre_equipo)
            if len(df.columns) >= 17: df = df.rename(columns={df.columns[16]: 'xG'})
            df['xG_val'] = df['xG'].fillna(0)
            df = df.rename(columns=TRADUCCIONES)
        elif tipo == "clasificacion":
            if 'Squad' in df.columns: df['Squad'] = df['Squad'].apply(limpiar_nombre_equipo)
            df = df.rename(columns=TRADUCCIONES)
        elif tipo == "fixture":
            df = df.rename(columns=TRADUCCIONES)
            if 'LOCAL' in df.columns: df['LOCAL'] = df['LOCAL'].apply(limpiar_nombre_equipo)
            if 'VISITANTE' in df.columns: df['VISITANTE'] = df['VISITANTE'].apply(limpiar_nombre_equipo)
        return df.dropna(how='all').reset_index(drop=True)
    except: return None

# ────────────────────────────────────────────────
# LÓGICA DE CUOTAS
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

def badge_cuota(val, es_minimo=False, tiene_valor=False):
    color_bg = "#b59410" if tiene_valor else ("#137031" if es_minimo else "#2d3139")
    color_text = "white" if tiene_valor else ("#00ff88" if es_minimo else "#ced4da")
    return f'<div style="display: flex; justify-content: center;"><span style="background-color: {color_bg}; color: {color_text}; padding: 5px 12px; border-radius: 6px; font-weight: bold; border: 1px solid #4b5563;">{val:.2f}</span></div>'

def procesar_cuotas(data, df_clas):
    if not data or not isinstance(data, list): return None
    rows = []
    puntos_dict = pd.Series(df_clas.PTS.values, index=df_clas.EQUIPO).to_dict() if df_clas is not None else {}
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
        val_h = False
        if home in puntos_dict and away in puntos_dict:
            pts_h, pts_a = puntos_dict[home], puntos_dict[away]
            prob_est = (pts_h + 5) / (pts_h + pts_a + 10)
            if h > ((1/prob_est) * 1.15): val_h = True
        rows.append({"FECHA": commence, "LOCAL": home, "VISITANTE": away, "1": h, "X": d, "2": a, "VAL_H": val_h})
    return pd.DataFrame(rows)

# ────────────────────────────────────────────────
# ESTILOS CSS
# ────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e5e7eb; }
    
    /* LOGO CORREGIDO */
    .main-logo-container {
        display: flex; justify-content: center; align-items: center;
        width: 100%; padding: 20px 0; margin-top: 0;
    }
    .main-logo-img { width: 50%; max-width: 450px; height: auto; }

    /* BOTONES CIAN UNIFICADOS */
    div.stButton > button { 
        background-color: transparent !important; color: #1ed7de !important; 
        border: 1px solid #1ed7de !important; font-weight: bold !important;
        width: 100%; transition: 0.3s;
    }
    div.stButton > button:hover { background-color: #1ed7de22 !important; color: white !important; }
    
    /* BOTON COMPETENCIAS (CIAN) */
    .comp-btn button { background-color: #1ed7de !important; color: #0e1117 !important; border: none !important; }

    /* SELECTOR CIAN */
    div[data-baseweb="select"] { border: 1px solid #1ed7de !important; border-radius: 4px; }
    
    /* ALINEACION TITULO Y BANDERA */
    .liga-header { display: flex; align-items: center; gap: 15px; margin: 20px 0; }
    .liga-header img { width: 40px; height: auto; display: block; }
    .liga-header span { font-size: 2rem; font-weight: bold; color: white; line-height: 1; }

    /* TABLAS */
    .table-container { border: 1px solid #1ed7de44; border-radius: 8px; background: #161b22; padding: 10px; overflow-x: auto; }
    th { background-color: #1f2937 !important; color: #1ed7de !important; text-align: center !important; }
    td { text-align: center !important; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# ESTRUCTURA
# ────────────────────────────────────────────────

# Logo centrado sin cortes
st.markdown('<div class="main-logo-container"><img src="https://i.postimg.cc/SKPzCcyV/33.png" class="main-logo-img"></div>', unsafe_allow_html=True)

if "liga_sel" not in st.session_state: st.session_state.liga_sel = None
if "vista_activa" not in st.session_state: st.session_state.vista_activa = "clas"
if "menu_op" not in st.session_state: st.session_state.menu_op = False

# Boton Competencias Cian
st.markdown('<div class="comp-btn">', unsafe_allow_html=True)
if st.button("COMPETENCIAS", key="main_comp"):
    st.session_state.menu_op = not st.session_state.menu_op
st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.menu_op:
    sel = st.selectbox("Ligas", ["Selecciona Liga"] + LIGAS_LISTA, label_visibility="collapsed")
    if sel != "Selecciona Liga":
        st.session_state.liga_sel = sel
        st.session_state.menu_op = False
        st.rerun()

if st.session_state.liga_sel:
    liga = st.session_state.liga_sel
    st.markdown(f'<div class="liga-header"><img src="{BANDERAS.get(liga)}"><span>{liga}</span></div>', unsafe_allow_html=True)
    
    # Sistema Acordeón Corregido (Botones que persisten)
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("Clasificación"): st.session_state.vista_activa = "clas"
    if col2.button("Stats Generales"): st.session_state.vista_activa = "stats"
    if col3.button("Ver Fixture"): st.session_state.vista_activa = "fix"
    if col4.button("Picks & Cuotas"): st.session_state.vista_activa = "odds"

    st.divider()

    view = st.session_state.vista_activa
    sufijo = MAPEO_ARCHIVOS.get(liga)
    
    if view == "odds":
        df_clas = cargar_excel(f"CLASIFICACION_LIGA_{sufijo}.xlsx", "clasificacion")
        st.subheader("⚔️ Comparador H2H")
        if df_clas is not None:
            eqs = sorted(df_clas['EQUIPO'].unique())
            c_h1, c_h2 = st.columns(2)
            l_eq = c_h1.selectbox("Local", eqs, index=0)
            v_eq = c_h2.selectbox("Visitante", eqs, index=1)
            
            d_l = df_clas[df_clas['EQUIPO'] == l_eq].iloc[0]
            d_v = df_clas[df_clas['EQUIPO'] == v_eq].iloc[0]
            
            st.markdown(f"""
            <div style="background: #1f2937; padding: 20px; border-radius: 12px; border-left: 5px solid #1ed7de;">
                <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #374151; padding: 10px 0;">
                    <span style="color: #1ed7de; font-weight: bold;">{d_l['PTS']}</span>
                    <span style="color: #9ca3af; text-transform: uppercase; font-size: 0.8rem;">Puntos</span>
                    <span style="color: #1ed7de; font-weight: bold;">{d_v['PTS']}</span>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 10px 0;">
                    <span style="color: white; font-weight: bold;">{d_l['G']}</span>
                    <span style="color: #9ca3af; text-transform: uppercase; font-size: 0.8rem;">Victorias</span>
                    <span style="color: white; font-weight: bold;">{d_v['G']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        raw_o = obtener_cuotas_api(liga)
        df_o = procesar_cuotas(raw_o, df_clas)
        if df_o is not None:
            df_res = df_o.apply(lambda r: pd.Series([r['FECHA'], r['LOCAL'], r['VISITANTE'], badge_cuota(r['1'], r['1']<r['2']), badge_cuota(r['X']), badge_cuota(r['2'], r['2']<r['1'])]), axis=1)
            df_res.columns = ['FECHA', 'LOCAL', 'VISITANTE', '1', 'X', '2']
            st.markdown(f'<div class="table-container">{df_res.to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)

    else:
        file_map = {"clas": "CLASIFICACION_LIGA", "stats": "RESUMEN_STATS", "fix": "CARTELERA_PROXIMOS"}
        type_map = {"clas": "clasificacion", "stats": "stats", "fix": "fixture"}
        df = cargar_excel(f"{file_map[view]}_{sufijo}.xlsx", type_map[view])
        
        if df is not None:
            if 'ÚLTIMOS 5' in df.columns: df['ÚLTIMOS 5'] = df['ÚLTIMOS 5'].apply(formatear_last_5)
            if 'POSESIÓN' in df.columns: df['POSESIÓN'] = df['POSESIÓN'].apply(html_barra_posesion)
            if 'xG' in df.columns: df['xG'] = df['xG'].apply(formatear_xg_badge)
            
            st.markdown(f'<div class="table-container">{df.to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)

st.write("---")
st.caption("InsideBet Official | scrapeo")
