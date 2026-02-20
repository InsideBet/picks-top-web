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
# FUNCIONES DE CARGA Y PROCESAMIENTO
# ────────────────────────────────────────────────

@st.cache_data(ttl=300)
def cargar_excel(ruta_archivo, tipo="general"):
    url = f"{BASE_URL}/{ruta_archivo}"
    try:
        df = pd.read_excel(url)
        if 'Home' in df.columns and 'Away' in df.columns:
            df = df.dropna(subset=['Home', 'Away'], how='all')
        if tipo == "stats":
            if 'Squad' in df.columns: df['Squad'] = df['Squad'].apply(limpiar_nombre_equipo)
            if len(df.columns) >= 17: df = df.rename(columns={df.columns[16]: 'xG'})
            df['xG_val'] = df['xG'].fillna(0)
            if 'Poss' in df.columns:
                df['Poss_num'] = df['Poss'].apply(lambda x: re.findall(r"\d+", str(x))[0] if re.findall(r"\d+", str(x)) else "0")
                df['Poss'] = df['Poss'].apply(html_barra_posesion)
            if 'xG' in df.columns: df['xG'] = df['xG'].apply(formatear_xg_badge)
            df = df.rename(columns=TRADUCCIONES)
        elif tipo == "clasificacion":
            if 'Squad' in df.columns: df['Squad'] = df['Squad'].apply(limpiar_nombre_equipo)
            df = df.rename(columns=TRADUCCIONES)
            if 'EQUIPO' in df.columns: df = df[df['EQUIPO'] != ""]
        elif tipo == "fixture":
            df = df.rename(columns=TRADUCCIONES)
            if 'LOCAL' in df.columns: df['LOCAL'] = df['LOCAL'].apply(limpiar_nombre_equipo)
            if 'VISITANTE' in df.columns: df['VISITANTE'] = df['VISITANTE'].apply(limpiar_nombre_equipo)
        return df.dropna(how='all').reset_index(drop=True)
    except: return None

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
    if not data or not isinstance(data, list): return None
    rows = []
    puntos_dict = pd.Series(df_clas.index.values + 1, index=df_clas.EQUIPO).to_dict() if df_clas is not None else {}
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
        rows.append({"FECHA": commence, "LOCAL": home, "VISITANTE": away, "1": h, "X": d, "2": a, "VAL_H": False})
    return pd.DataFrame(rows)

# ────────────────────────────────────────────────
# ESTILOS CSS
# ────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e5e7eb; }
    .table-container { width: 100%; overflow-x: auto; border: 1px solid #1ed7de44; border-radius: 8px; margin-bottom: 20px; background-color: #161b22; }
    table { width: 100%; border-collapse: collapse; }
    th { background-color: #1f2937 !important; color: #1ed7de !important; padding: 12px; border: 1px solid #374151; font-size: 13px; text-transform: uppercase; }
    td { padding: 12px; border: 1px solid #374151; text-align: center !important; }
    div.stButton > button { background-color: transparent !important; color: #1ed7de !important; border: 1px solid #1ed7de !important; font-weight: bold !important; transition: 0.3s; width: 100%; }
    div.stButton > button:hover { background-color: #1ed7de22 !important; border: 1px solid #1ed7de !important; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# ESTRUCTURA DE LA APP
# ────────────────────────────────────────────────
st.markdown('<div style="text-align:center; padding:20px;"><img src="https://i.postimg.cc/SKPzCcyV/33.png" style="width:40%;"></div>', unsafe_allow_html=True)

if "liga_sel" not in st.session_state: st.session_state.liga_sel = None
if "vista_activa" not in st.session_state: st.session_state.vista_activa = None
if "menu_op" not in st.session_state: st.session_state.menu_op = False
if "h2h_op" not in st.session_state: st.session_state.h2h_op = False
if "conf_op" not in st.session_state: st.session_state.conf_op = False

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
    if col1.button("Clasificación", use_container_width=True): 
        st.session_state.vista_activa = "clas" if st.session_state.vista_activa != "clas" else None
        st.rerun()
    if col2.button("Stats Generales", use_container_width=True): 
        st.session_state.vista_activa = "stats" if st.session_state.vista_activa != "stats" else None
        st.rerun()
    if col3.button("Ver Fixture", use_container_width=True): 
        st.session_state.vista_activa = "fix" if st.session_state.vista_activa != "fix" else None
        st.rerun()
    if col4.button("Picks & Cuotas", use_container_width=True): 
        st.session_state.vista_activa = "odds" if st.session_state.vista_activa != "odds" else None
        st.rerun()

    view = st.session_state.vista_activa
    if view:
        sufijo = MAPEO_ARCHIVOS.get(liga)
        df_clas_base = cargar_excel(f"CLASIFICACION_LIGA_{sufijo}.xlsx", "clasificacion")
        df_stats_base = cargar_excel(f"RESUMEN_STATS_{sufijo}.xlsx", "stats")

        # 1. VISTA CLASIFICACIÓN (RESTAURADA)
        if view == "clas" and df_clas_base is not None:
            df_v = df_clas_base.copy()
            if 'ÚLTIMOS 5' in df_v.columns:
                df_v['FORMA'] = df_v['ÚLTIMOS 5'].apply(grafico_picos_forma)
                df_v['ÚLTIMOS 5'] = df_v['ÚLTIMOS 5'].apply(formatear_last_5)
            cols = ['POS', 'EQUIPO', 'PJ', 'G', 'E', 'P', 'GF', 'GC', 'DG', 'PTS', 'ÚLTIMOS 5', 'FORMA']
            st.markdown(f'<div class="table-container">{df_v[cols].style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

        # 2. VISTA STATS (RESTAURADA)
        elif view == "stats" and df_stats_base is not None:
            df_v = df_stats_base.copy()
            cols_show = ['EQUIPO', 'PJ', 'POSESIÓN', 'GOLES', 'ASISTENCIAS', 'xG', 'AMARILLAS', 'ROJAS']
            st.markdown(f'<div class="table-container">{df_v[cols_show].style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

        # 3. VISTA FIXTURE (FDR ACTUALIZADO)
        elif view == "fix" and df_clas_base is not None:
            st.subheader("🗓️ Cartelera Próximos Partidos")
            top_6 = df_clas_base.head(6)['EQUIPO'].tolist()
            solo_interes = st.checkbox("⭐ Ver solo partidos de interés (Top 6)")
            df_fix = cargar_excel(f"CARTELERA_PROXIMOS_{sufijo}.xlsx", "fixture")
            if df_fix is not None:
                pos_dict = pd.Series(df_clas_base.index.values + 1, index=df_clas_base.EQUIPO).to_dict()
                if solo_interes:
                    df_fix = df_fix[df_fix['LOCAL'].isin(top_6) | df_fix['VISITANTE'].isin(top_6)]
                df_fix['LOCAL'] = df_fix['LOCAL'].apply(lambda x: obtener_fdr_html(x, pos_dict, len(df_clas_base)))
                df_fix['VISITANTE'] = df_fix['VISITANTE'].apply(lambda x: obtener_fdr_html(x, pos_dict, len(df_clas_base)))
                html = df_fix[['FECHA', 'HORA', 'LOCAL', 'VISITANTE', 'ESTADIO']].style.hide(axis="index").to_html(escape=False)
                st.markdown(f'<div class="table-container">{html}</div>', unsafe_allow_html=True)
                st.markdown("""<div style="background:#161b22; padding:15px; border-radius:8px; border:1px solid #1ed7de44;"><div style="display:flex; gap:20px;"><span><span style="height:8px; width:8px; background-color:#137031; border-radius:50%; display:inline-block;"></span> <b>Elite:</b> Top 5</span><span><span style="height:8px; width:8px; background-color:#b59410; border-radius:50%; display:inline-block;"></span> <b>Media Tabla</b></span><span><span style="height:8px; width:8px; background-color:#821f1f; border-radius:50%; display:inline-block;"></span> <b>Zona Crítica</b></span></div></div>""", unsafe_allow_html=True)

        # 4. VISTA PICKS (RESTAURADA)
        elif view == "odds" and df_clas_base is not None:
            if st.button("⚔️ COMPARADOR H2H", use_container_width=True): st.session_state.h2h_op = not st.session_state.h2h_op
            if st.session_state.h2h_op and df_stats_base is not None:
                equipos = sorted(df_clas_base['EQUIPO'].unique())
                f1, f2 = st.columns(2)
                e_l = f1.selectbox("Local", equipos, index=0)
                e_v = f2.selectbox("Visitante", equipos, index=1)
                try:
                    c_l, c_v = df_clas_base[df_clas_base['EQUIPO']==e_l].iloc[0], df_clas_base[df_clas_base['EQUIPO']==e_v].iloc[0]
                    s_l, s_v = df_stats_base[df_stats_base['EQUIPO']==e_l].iloc[0], df_stats_base[df_stats_base['EQUIPO']==e_v].iloc[0]
                    labels = ["PTS", "POSS", "GF", "xG", "VICT"]
                    radar_l = [min(c_l['PTS']*1.5, 100), float(s_l['Poss_num']), min(c_l['GF']*1.2, 100), min(float(s_l['xG_val'])*20, 100), min(c_l['G']*5, 100)]
                    radar_v = [min(c_v['PTS']*1.5, 100), float(s_v['Poss_num']), min(c_v['GF']*1.2, 100), min(float(s_v['xG_val'])*20, 100), min(c_v['G']*5, 100)]
                    c_radar, c_info = st.columns([1, 2])
                    c_radar.markdown(generar_radar_svg(radar_l, radar_v, labels), unsafe_allow_html=True)
                    c_info.markdown(f"""<div style="background:#1f2937; padding:15px; border-radius:12px; border:1px solid #1ed7de44;"><div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #2d3139;"><span style="color:#1ed7de;">{c_l['PTS']}</span><span style="color:#9ca3af;">PUNTOS</span><span style="color:#1ed7de;">{c_v['PTS']}</span></div><div style="display:flex; justify-content:space-between; padding:8px 0;">{grafico_picos_forma(c_l['ÚLTIMOS 5'], "left")}<span style="color:#9ca3af;">FORMA</span>{grafico_picos_forma(c_v['ÚLTIMOS 5'], "right")}</div></div>""", unsafe_allow_html=True)
                except: st.warning("Datos insuficientes.")

            st.subheader("📊 Picks & Cuotas")
            raw = obtener_cuotas_api(liga)
            df_odds = procesar_cuotas(raw, df_clas_base)
            if df_odds is not None:
                def color_cuota(r):
                    m = min(r['1'], r['X'], r['2'])
                    r['1'] = badge_cuota(r['1'], r['1']==m)
                    r['X'] = badge_cuota(r['X'], r['X']==m)
                    r['2'] = badge_cuota(r['2'], r['2']==m)
                    return r
                st.markdown(f'<div class="table-container">{df_odds.apply(color_cuota, axis=1)[["FECHA","LOCAL","VISITANTE","1","X","2"]].style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

st.write("---")
st.caption("InsideBet Official | scrapeo")
