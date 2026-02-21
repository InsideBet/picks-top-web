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
# FUNCIONES DE FORMATO Y LÓGICA
# ────────────────────────────────────────────────

def limpiar_nombre_equipo(nombre):
    if pd.isna(nombre) or str(nombre).lower() == 'nan': return ""
    txt = str(nombre).strip()
    txt = re.sub(r'^[a-z]{2,3}\s+', '', txt, flags=re.IGNORECASE)
    txt = re.sub(r'\s+[a-z]{2,3}$', '', txt, flags=re.IGNORECASE)
    return txt.strip()

def calcular_score_confianza(equipo, df_clas, df_stats):
    """Calcula el porcentaje de confianza para un equipo basado en datos actuales."""
    try:
        c = df_clas[df_clas['EQUIPO'] == equipo].iloc[0]
        s = df_stats[df_stats['EQUIPO'] == equipo].iloc[0]
        pts_pj = c['PTS'] / (c['PJ'] if c['PJ'] > 0 else 1)
        # Algoritmo: xG (40%) + Puntos/PJ (40%) + Forma (20%)
        score = (float(s['xG_val']) * 0.4) + (pts_pj * 15) + (str(c['ÚLTIMOS 5']).count('W') * 5)
        return min(int(score * 2), 100)
    except:
        return 0

def html_barra_posesion(valor):
    try:
        num_str = str(valor).replace('%', '').strip()
        num_clean = re.findall(r"[-+]?\d*\.\d+|\d+", num_str)[0]
        num = float(num_clean)
        percent = min(max(int(num), 0), 100)
        return f'''
        <div style="position: relative; width: 100%; background-color: #2d3139; border-radius: 4px; height: 18px; overflow: hidden; border: 1px solid #4b5563;">
            <div style="width: {percent}%; background-color: #1ed7de; height: 100%;"></div>
            <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: white; font-size: 10px; font-weight: bold;">
                {percent}%
            </div>
        </div>
        '''
    except: return valor

def grafico_picos_forma(valor, alineacion="left"):
    if pd.isna(valor) or valor == "": return ""
    letras = list(str(valor).upper().replace(" ", ""))[:5]
    if not letras: return ""
    mapeo_y = {'W': 4, 'D': 11, 'L': 18}
    colores_puntos = {'W': '#137031', 'D': '#b59410', 'L': '#821f1f'}
    puntos_coords = []
    puntos_svg = []
    for i, l in enumerate(letras):
        x = 10 + (i * 25) 
        y = mapeo_y.get(l, 11)
        puntos_coords.append(f"{x},{y}")
        puntos_svg.append(f'<circle cx="{x}" cy="{y}" r="3" fill="{colores_puntos.get(l, "#4b5563")}" stroke="#0e1117" stroke-width="0.5" />')
    path_d = "M " + " L ".join(puntos_coords)
    return f'<div style="width: 100%; height: 30px; display: flex; align-items: center; justify-content: {"flex-start" if alineacion=="left" else "flex-end"};"><svg width="130" height="22" viewBox="0 0 130 22"><path d="{path_d}" fill="none" stroke="#1ed7de" stroke-width="1.2" opacity="0.4" />{"".join(puntos_svg)}</svg></div>'

def generar_radar_svg(val_l, val_v, labels):
    size = 200
    center = size / 2
    radius = 70
    def get_coords(value, angle, max_val=100):
        v = float(value) if pd.notna(value) else 0
        r = (min(v, max_val) / max_val) * radius
        return f"{center + r * np.cos(angle - np.pi/2)},{center + r * np.sin(angle - np.pi/2)}"
    angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False)
    pts_l = [get_coords(v, a) for v, a in zip(val_l, angles)]
    pts_v = [get_coords(v, a) for v, a in zip(val_v, angles)]
    return f'''<svg width="100%" height="{size}" viewBox="0 0 {size} {size}"><polygon points="{" ".join(pts_l)}" fill="#1ed7de22" stroke="#1ed7de" stroke-width="2" /><polygon points="{" ".join(pts_v)}" fill="#b5941022" stroke="#b59410" stroke-width="2" />{''.join([f'<text x="{center + (radius+20)*np.cos(a-np.pi/2)}" y="{center + (radius+20)*np.sin(a-np.pi/2)}" fill="#9ca3af" font-size="9" text-anchor="middle">{l}</text>' for l, a in zip(labels, angles)])}</svg>'''

@st.cache_data(ttl=300)
def cargar_excel(ruta_archivo, tipo="general"):
    url = f"{BASE_URL}/Estadisticas_Jugadores/{ruta_archivo}" if "SUPER_STATS" in ruta_archivo else f"{BASE_URL}/{ruta_archivo}"
    try:
        df = pd.read_excel(url)
        if tipo == "stats":
            if 'Squad' in df.columns: df['Squad'] = df['Squad'].apply(limpiar_nombre_equipo)
            if len(df.columns) >= 17: df = df.rename(columns={df.columns[16]: 'xG'})
            df['xG_val'] = df['xG'].fillna(0)
            if 'Poss' in df.columns:
                df['Poss_num'] = df['Poss'].apply(lambda x: re.findall(r"\d+", str(x))[0] if re.findall(r"\d+", str(x)) else "0")
                df['Poss'] = df['Poss'].apply(html_barra_posesion)
            cols_ok = ['Squad', 'MP', 'Poss', 'Poss_num', 'Gls', 'Ast', 'CrdY', 'CrdR', 'xG', 'xG_val']
            df = df[[c for c in cols_ok if c in df.columns]].rename(columns=TRADUCCIONES)
        elif tipo == "clasificacion":
            if 'Squad' in df.columns: df['Squad'] = df['Squad'].apply(limpiar_nombre_equipo)
            df = df.drop(columns=[c for c in ['Notes', 'Goalkeeper', 'Attendance', 'Pts/MP'] if c in df.columns]).rename(columns=TRADUCCIONES)
            if 'EQUIPO' in df.columns: df = df[df['EQUIPO'] != ""]
        return df.dropna(how='all').reset_index(drop=True)
    except: return None

def obtener_cuotas_api(liga_nombre):
    sport_key = MAPEO_ODDS_API.get(liga_nombre)
    if not sport_key or not API_KEY: return None
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
    try:
        response = requests.get(url, params={'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h', 'oddsFormat': 'decimal'})
        return response.json()
    except: return None

def badge_cuota(val, es_minimo=False, tiene_valor=False):
    color_bg = "#b59410" if tiene_valor else ("#137031" if es_minimo else "#2d3139")
    return f'<div style="display: flex; justify-content: center;"><span style="background-color: {color_bg}; color: white; padding: 5px 12px; border-radius: 6px; font-weight: bold; font-size: 13px; border: 1px solid #4b5563;">{val:.2f}{" ⭐" if tiene_valor else ""}</span></div>'

# ────────────────────────────────────────────────
# ESTILOS CSS (MEJORADO)
# ────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e5e7eb; }
    .main-logo-container { text-align: center; width: 100%; padding: 20px 0; }
    .main-logo-img { width: 50%; max-width: 500px; margin: 0 auto; }
    .table-container { width: 100%; overflow-x: auto; border: 1px solid #1ed7de44; border-radius: 8px; margin-bottom: 20px; background-color: #161b22; }
    th { background-color: #1f2937 !important; color: #1ed7de !important; padding: 12px; border: 1px solid #374151; }
    td { padding: 12px; border: 1px solid #374151; text-align: center !important; }
    
    /* Efecto de botón activo */
    .stButton > button { background-color: transparent !important; color: #1ed7de !important; border: 1px solid #1ed7de !important; width: 100%; transition: 0.3s; }
    .stButton > button:active, .stButton > button:focus { background-color: #1ed7de !important; color: #0e1117 !important; box-shadow: 0 0 15px #1ed7de88; }
    
    .header-container { display: flex; align-items: center; gap: 15px; margin: 25px 0; }
    .header-title { color: white !important; font-size: 2rem; font-weight: bold; margin: 0; }
    .badge-conf { padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; margin-left: 5px; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# LÓGICA DE INTERFAZ
# ────────────────────────────────────────────────
st.markdown('<div class="main-logo-container"><img src="https://i.postimg.cc/SKPzCcyV/33.png" class="main-logo-img"></div>', unsafe_allow_html=True)

if "liga_sel" not in st.session_state: st.session_state.liga_sel = None
if "vista_activa" not in st.session_state: st.session_state.vista_activa = "clas"

if st.button("COMPETENCIAS", use_container_width=True):
    st.session_state.menu_op = not st.session_state.get('menu_op', False)

if st.session_state.get('menu_op'):
    sel = st.selectbox("Ligas", ["Selecciona Liga"] + LIGAS_LISTA, label_visibility="collapsed")
    if sel != "Selecciona Liga":
        st.session_state.liga_sel = sel
        st.session_state.menu_op = False
        st.rerun()

if st.session_state.liga_sel:
    liga = st.session_state.liga_sel
    st.markdown(f'<div class="header-container"><img src="{BANDERAS.get(liga, "")}" style="width:40px;"><span class="header-title">{liga}</span></div>', unsafe_allow_html=True)
    
    cols = st.columns(5)
    btn_labels = ["Clasificación", "Stats Equipos", "Jugadores", "Fixture", "Picks"]
    btn_keys = ["clas", "stats", "players", "fix", "odds"]
    
    for i, label in enumerate(btn_labels):
        if cols[i].button(label, use_container_width=True):
            st.session_state.vista_activa = btn_keys[i]
            st.rerun()

    st.divider()
    view = st.session_state.vista_activa
    sufijo = MAPEO_ARCHIVOS.get(liga)
    df_clas_base = cargar_excel(f"CLASIFICACION_LIGA_{sufijo}.xlsx", "clasificacion")
    df_stats_base = cargar_excel(f"RESUMEN_STATS_{sufijo}.xlsx", "stats")

    if view == "players":
        df_p = cargar_excel(f"SUPER_STATS_{sufijo}.xlsx", "general")
        if df_p is not None:
            f1, f2, f3, f4 = st.columns([2, 2, 2, 2])
            with f1: equipo_f = st.selectbox("Filtrar Equipo", ["Todos"] + sorted(df_p['Squad'].unique().tolist()))
            with f2: p_sel = st.multiselect("Posición", df_p['Pos'].unique(), default=df_p['Pos'].unique())
            with f3: m_min = st.slider("Minutos", 0, int(df_p['Min'].max()), 90)
            with f4: p_busq = st.text_input("🔍 Jugador", "").strip().lower()

            mask = (df_p['Min'] >= m_min) & (df_p['Pos'].isin(p_sel))
            if equipo_f != "Todos": mask = mask & (df_p['Squad'] == equipo_f)
            if p_busq: mask = mask & (df_p['Player'].str.lower().str.contains(p_busq))
            
            df_f = df_p[mask].copy()
            t1, t2 = st.tabs(["🎯 ATAQUE & REMATES", "🛡️ DISCIPLINA"])
            with t1:
                st.markdown(f'<div class="table-container">{df_f[["Player", "Squad", "Gls", "Ast", "Sh", "SoT"]].rename(columns=TRADUCCIONES).style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)
            with t2:
                st.markdown(f'<div class="table-container">{df_f[["Player", "Squad", "Fls", "Fld", "CrdY", "CrdR"]].rename(columns=TRADUCCIONES).style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

    elif view == "odds":
        raw = obtener_cuotas_api(liga)
        if raw:
            st.subheader("📊 Picks & Análisis de Valor")
            df_odds = []
            for m in raw:
                h, a = m['home_team'], m['away_team']
                # Cálculo de confianza en tiempo real para la tabla
                conf_h = calcular_score_confianza(h, df_clas_base, df_stats_base)
                conf_a = calcular_score_confianza(a, df_clas_base, df_stats_base)
                
                # Extracción de cuotas (ejemplo simplificado Bet365)
                try:
                    outcomes = m['bookmakers'][0]['markets'][0]['outcomes']
                    odds = {o['name']: o['price'] for o in outcomes}
                    draw_odd = next(o['price'] for o in outcomes if o['name'] not in [h, a])
                    df_odds.append({
                        "FECHA": pd.to_datetime(m['commence_time']).strftime('%d/%m'),
                        "LOCAL": f"{h} <span class='badge-conf' style='background:#1ed7de22; color:#1ed7de'>{conf_h}%</span>",
                        "VISITANTE": f"{a} <span class='badge-conf' style='background:#1ed7de22; color:#1ed7de'>{conf_a}%</span>",
                        "1": badge_cuota(odds[h], odds[h] < 2.0), "X": badge_cuota(draw_odd), "2": badge_cuota(odds[a], odds[a] < 2.0)
                    })
                except: continue
            
            st.markdown(f'<div class="table-container">{pd.DataFrame(df_odds).style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

    else:
        # Lógica para Clasificación y Stats Equipos (Manteniendo tu formato HTML)
        archivo = f"CLASIFICACION_LIGA_{sufijo}.xlsx" if view == "clas" else f"RESUMEN_STATS_{sufijo}.xlsx"
        df = cargar_excel(archivo, tipo=view)
        if df is not None:
            if 'ÚLTIMOS 5' in df.columns: df['ÚLTIMOS 5'] = df['ÚLTIMOS 5'].apply(grafico_picos_forma)
            st.markdown(f'<div class="table-container">{df.style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

st.write("---")
st.caption("InsideBet Official | scrapeo")
