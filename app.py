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
# FUNCIONES DE FORMATO (ORIGINALES)
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
    svg = f'''<div style="width: 100%; height: 30px; display: flex; align-items: center; justify-content: {'flex-start' if alineacion=='left' else 'flex-end'};"><svg width="130" height="22" viewBox="0 0 130 22" preserveAspectRatio="xMidYMid meet"><path d="{path_d}" fill="none" stroke="#1ed7de" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" opacity="0.4" />{''.join(puntos_svg)}</svg></div>'''
    return svg

def generar_radar_svg(val_l, val_v, labels):
    size = 200
    center = size / 2
    radius = 70
    def get_coords(value, angle, max_val=100):
        v = float(value) if pd.notna(value) else 0
        r = (min(v, max_val) / max_val) * radius
        x = center + r * np.cos(angle - np.pi/2)
        y = center + r * np.sin(angle - np.pi/2)
        return f"{x},{y}"
    angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False)
    grid = ""
    for r_f in [0.25, 0.5, 0.75, 1.0]:
        pts = [f"{center + (radius*r_f)*np.cos(a-np.pi/2)},{center + (radius*r_f)*np.sin(a-np.pi/2)}" for a in angles]
        grid += f'<polygon points="{" ".join(pts)}" fill="none" stroke="#4b5563" stroke-width="0.5" stroke-dasharray="2,2" />'
    pts_l = [get_coords(v, a) for v, a in zip(val_l, angles)]
    pts_v = [get_coords(v, a) for v, a in zip(val_v, angles)]
    radar = f'''<svg width="100%" height="{size}" viewBox="0 0 {size} {size}">{grid}<polygon points="{" ".join(pts_l)}" fill="#1ed7de22" stroke="#1ed7de" stroke-width="2" /><polygon points="{" ".join(pts_v)}" fill="#b5941022" stroke="#b59410" stroke-width="2" />{''.join([f'<text x="{center + (radius+20)*np.cos(a-np.pi/2)}" y="{center + (radius+20)*np.sin(a-np.pi/2)}" fill="#9ca3af" font-size="9" text-anchor="middle">{l}</text>' for l, a in zip(labels, angles)])}</svg>'''
    return radar

def formatear_last_5(valor):
    if pd.isna(valor) or valor == "": return ""
    trad = {'W': 'G', 'L': 'P', 'D': 'E'}
    letras = list(str(valor).upper().replace(" ", ""))[:5]
    html_str = '<div style="display: flex; gap: 4px; justify-content: center;">'
    for l in letras:
        clase_color = "#137031" if l == 'W' else "#821f1f" if l == 'L' else "#82711f" if l == 'D' else "#2d3139"
        html_str += f'<span style="background-color: {clase_color}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; min-width: 20px; text-align: center;">{trad.get(l, l)}</span>'
    return html_str + '</div>'

def obtener_fdr_html(nombre_equipo, puntos_dict, total_equipos):
    pos = puntos_dict.get(nombre_equipo, 10)
    if pos <= 5: color = "#137031"
    elif pos > (total_equipos - 3): color = "#821f1f"
    else: color = "#b59410"
    return f'<div style="display: flex; align-items: center; justify-content: center; gap: 8px;">{nombre_equipo} <span style="height: 8px; width: 8px; background-color: {color}; border-radius: 50%; display: inline-block;"></span></div>'

# ────────────────────────────────────────────────
# FUNCIONES DE CARGA
# ────────────────────────────────────────────────

@st.cache_data(ttl=300)
def cargar_excel(ruta_archivo, tipo="general"):
    url = f"{BASE_URL}/{ruta_archivo}"
    try:
        df = pd.read_excel(url)
        if tipo == "stats":
            if 'Squad' in df.columns: df['Squad'] = df['Squad'].apply(limpiar_nombre_equipo)
            if len(df.columns) >= 17: df = df.rename(columns={df.columns[16]: 'xG'})
            df['xG_val'] = df['xG'].fillna(0)
            df['Poss_num'] = df['Poss'].apply(lambda x: re.findall(r"\d+", str(x))[0] if re.findall(r"\d+", str(x)) else "0")
            df['Poss'] = df['Poss'].apply(html_barra_posesion)
            df['xG'] = df['xG'].apply(formatear_xg_badge)
            df = df.rename(columns=TRADUCCIONES)
        elif tipo == "clasificacion":
            if 'Squad' in df.columns: df['Squad'] = df['Squad'].apply(limpiar_nombre_equipo)
            df = df.rename(columns=TRADUCCIONES)
        elif tipo == "fixture":
            df = df.rename(columns=TRADUCCIONES)
            if 'LOCAL' in df.columns: df['LOCAL'] = df['LOCAL'].apply(limpiar_nombre_equipo)
            if 'VISITANTE' in df.columns: df['VISITANTE'] = df['VISITANTE'].apply(limpiar_nombre_equipo)
        return df.reset_index(drop=True)
    except: return None

# ... (Funciones de Cuotas Api y Badge Cuota)
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
    label = " ⭐" if tiene_valor else ""
    return f'<div style="display: flex; justify-content: center;"><span style="background-color: {color_bg}; color: {color_text}; padding: 5px 12px; border-radius: 6px; font-weight: bold; font-size: 13px; min-width: 60px; text-align: center; border: 1px solid #4b5563;">{val:.2f}{label}</span></div>'

def procesar_cuotas(data, df_clas):
    if not data: return None
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

# ────────────────────────────────────────────────
# ESTILOS CSS
# ────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e5e7eb; }
    .table-container { width: 100%; overflow-x: auto; border: 1px solid #1ed7de44; border-radius: 8px; margin-bottom: 20px; background-color: #161b22; }
    table { width: 100%; border-collapse: collapse; }
    th { background-color: #1f2937 !important; color: #1ed7de !important; padding: 12px; border: 1px solid #374151; font-size: 13px; }
    td { padding: 12px; border: 1px solid #374151; text-align: center !important; }
    div.stButton > button { background-color: transparent !important; color: #1ed7de !important; border: 1px solid #1ed7de !important; width: 100%; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# ESTRUCTURA
# ────────────────────────────────────────────────
st.markdown('<div style="text-align:center; padding:20px;"><img src="https://i.postimg.cc/SKPzCcyV/33.png" style="width:40%;"></div>', unsafe_allow_html=True)

if "liga_sel" not in st.session_state: st.session_state.liga_sel = None
if "vista_activa" not in st.session_state: st.session_state.vista_activa = None
if "menu_op" not in st.session_state: st.session_state.menu_op = False

if st.button("COMPETENCIAS", use_container_width=True):
    st.session_state.menu_op = not st.session_state.menu_op

if st.session_state.menu_op:
    sel = st.selectbox("Ligas", ["Selecciona Liga"] + LIGAS_LISTA)
    if sel != "Selecciona Liga":
        st.session_state.liga_sel = sel
        st.session_state.menu_op = False
        st.session_state.vista_activa = "clas"
        st.rerun()

if st.session_state.liga_sel:
    liga = st.session_state.liga_sel
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("Clasificación", use_container_width=True): st.session_state.vista_activa = "clas"; st.rerun()
    if col2.button("Stats Generales", use_container_width=True): st.session_state.vista_activa = "stats"; st.rerun()
    if col3.button("Ver Fixture", use_container_width=True): st.session_state.vista_activa = "fix"; st.rerun()
    if col4.button("Picks & Cuotas", use_container_width=True): st.session_state.vista_activa = "odds"; st.rerun()

    view = st.session_state.vista_activa
    if view:
        sufijo = MAPEO_ARCHIVOS.get(liga)
        
        # VISTA CLASIFICACIÓN (RESTAURADA)
        if view == "clas":
            df = cargar_excel(f"CLASIFICACION_LIGA_{sufijo}.xlsx", "clasificacion")
            if df is not None:
                df['FORMA'] = df['ÚLTIMOS 5'].apply(grafico_picos_forma)
                df['ÚLTIMOS 5'] = df['ÚLTIMOS 5'].apply(formatear_last_5)
                cols = ['POS', 'EQUIPO', 'PJ', 'G', 'E', 'P', 'GF', 'GC', 'DG', 'PTS', 'ÚLTIMOS 5', 'FORMA']
                st.markdown(f'<div class="table-container">{df[cols].style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

        # VISTA STATS (RESTAURADA)
        elif view == "stats":
            df = cargar_excel(f"RESUMEN_STATS_{sufijo}.xlsx", "stats")
            if df is not None:
                cols_s = ['EQUIPO', 'PJ', 'POSESIÓN', 'GOLES', 'ASISTENCIAS', 'xG', 'AMARILLAS', 'ROJAS']
                st.markdown(f'<div class="table-container">{df[cols_s].style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

        # VISTA FIXTURE (CON FDR)
        elif view == "fix":
            df_c = cargar_excel(f"CLASIFICACION_LIGA_{sufijo}.xlsx", "clasificacion")
            df_f = cargar_excel(f"CARTELERA_PROXIMOS_{sufijo}.xlsx", "fixture")
            if df_f is not None and df_c is not None:
                pos_dict = pd.Series(df_c.index.values + 1, index=df_c.EQUIPO).to_dict()
                top_6 = df_c.head(6)['EQUIPO'].tolist()
                solo_int = st.checkbox("⭐ Ver solo partidos de interés")
                if solo_int: df_f = df_f[df_f['LOCAL'].isin(top_6) | df_f['VISITANTE'].isin(top_6)]
                df_f['LOCAL'] = df_f['LOCAL'].apply(lambda x: obtener_fdr_html(x, pos_dict, len(df_c)))
                df_f['VISITANTE'] = df_f['VISITANTE'].apply(lambda x: obtener_fdr_html(x, pos_dict, len(df_c)))
                st.markdown(f'<div class="table-container">{df_f[["FECHA", "HORA", "LOCAL", "VISITANTE", "ESTADIO"]].style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

        # VISTA ODDS (RESTURADA)
        elif view == "odds":
            df_c = cargar_excel(f"CLASIFICACION_LIGA_{sufijo}.xlsx", "clasificacion")
            raw = obtener_cuotas_api(liga)
            df_o = procesar_cuotas(raw, df_c)
            if df_o is not None:
                def color_o(r):
                    m = min(r['1'], r['X'], r['2'])
                    r['1'], r['X'], r['2'] = badge_cuota(r['1'], r['1']==m), badge_cuota(r['X'], r['X']==m), badge_cuota(r['2'], r['2']==m)
                    return r
                st.markdown(f'<div class="table-container">{df_o.apply(color_o, axis=1).style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

st.write("---")
st.caption("InsideBet Official | scrapeo")
