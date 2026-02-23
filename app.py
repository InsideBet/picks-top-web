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
# FUNCIONES DE FORMATO (ORIGINALES SIN TOCAR)
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
    svg = f'''
    <div style="width: 100%; height: 30px; display: flex; align-items: center; justify-content: {'flex-start' if alineacion=='left' else 'flex-end'};">
        <svg width="130" height="22" viewBox="0 0 130 22" preserveAspectRatio="xMidYMid meet">
            <path d="{path_d}" fill="none" stroke="#1ed7de" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" opacity="0.4" />
            {''.join(puntos_svg)}
        </svg>
    </div>
    '''
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
    radar = f'''
    <svg width="100%" height="{size}" viewBox="0 0 {size} {size}">
        {grid}
        <polygon points="{" ".join(pts_l)}" fill="#1ed7de22" stroke="#1ed7de" stroke-width="2" />
        <polygon points="{" ".join(pts_v)}" fill="#b5941022" stroke="#b59410" stroke-width="2" />
        {''.join([f'<text x="{center + (radius+20)*np.cos(a-np.pi/2)}" y="{center + (radius+20)*np.sin(a-np.pi/2)}" fill="#9ca3af" font-size="9" text-anchor="middle">{l}</text>' for l, a in zip(labels, angles)])}
    </svg>
    '''
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

# ────────────────────────────────────────────────
# FUNCIONES DE CARGA Y PROCESAMIENTO
# ────────────────────────────────────────────────

@st.cache_data(ttl=300)
def cargar_excel(ruta_archivo, tipo="general"):
    if "picks_finales_fiables" in ruta_archivo:
        url = f"{BASE_URL}/{ruta_archivo}"
    elif "SUPER_STATS" in ruta_archivo:
        url = f"{BASE_URL}/Estadisticas_Jugadores/{ruta_archivo}"
    else:
        url = f"{BASE_URL}/{ruta_archivo}"
        
    try:
        # Se añade soporte para el CSV de scrapeo
        if ruta_archivo.endswith('.csv'):
            df = pd.read_csv(url)
        else:
            df = pd.read_excel(url)
            
        if 'Home' in df.columns and 'Away' in df.columns:
            df = df.dropna(subset=['Home', 'Away'], how='all')
        if tipo == "stats":
            if 'Squad' in df.columns:
                df['Squad'] = df['Squad'].apply(limpiar_nombre_equipo)
            if len(df.columns) >= 17:
                df = df.rename(columns={df.columns[16]: 'xG'})
            df['xG_val'] = df['xG'].fillna(0)
            if 'Poss' in df.columns:
                df['Poss_num'] = df['Poss'].apply(lambda x: re.findall(r"\d+", str(x))[0] if re.findall(r"\d+", str(x)) else "0")
                df['Poss'] = df['Poss'].apply(html_barra_posesion)
            if 'xG' in df.columns: df['xG'] = df['xG'].apply(formatear_xg_badge)
            cols_ok = ['Squad', 'MP', 'Poss', 'Poss_num', 'Gls', 'Ast', 'CrdY', 'CrdR', 'xG', 'xG_val']
            df = df[[c for c in cols_ok if c in df.columns]]
            df = df.rename(columns=TRADUCCIONES)
        elif tipo == "clasificacion":
            if 'Squad' in df.columns:
                df['Squad'] = df['Squad'].apply(limpiar_nombre_equipo)
            drop_c = ['Notes', 'Goalkeeper', 'Top Team Scorer', 'Attendance', 'Pts/MP', 'Pts/PJ']
            df = df.drop(columns=[c for c in drop_c if c in df.columns])
            df = df.rename(columns=TRADUCCIONES)
            if 'EQUIPO' in df.columns:
                df = df[df['EQUIPO'] != ""]
            cols = list(df.columns)
            if 'EQUIPO' in cols and 'PTS' in cols:
                cols.remove('PTS')
                idx = cols.index('EQUIPO')
                cols.insert(idx + 1, 'PTS')
                df = df[cols]
        elif tipo == "fixture":
            drop_f = ['Round', 'Day', 'Score', 'Referee', 'Match Report', 'Notes', 'Attendance', 'Wk']
            df = df.drop(columns=[c for c in drop_f if c in df.columns])
            df = df.rename(columns=TRADUCCIONES)
            if 'LOCAL' in df.columns:
                df['LOCAL'] = df['LOCAL'].apply(limpiar_nombre_equipo)
            if 'VISITANTE' in df.columns:
                df['VISITANTE'] = df['VISITANTE'].apply(limpiar_nombre_equipo)
            df = df[df['LOCAL'] != ""]
            if 'FECHA' in df.columns: 
                df['FECHA'] = df['FECHA'].apply(lambda x: str(x).split(' ')[0] if pd.notna(x) else "TBD")
            if 'HORA' in df.columns: 
                df['HORA'] = df['HORA'].fillna("Por definir")
        return df.dropna(how='all').reset_index(drop=True)
    except: 
        return None

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
    .main-logo-container { text-align: center; width: 100%; padding: 20px 0; }
    .main-logo-img { width: 50%; max-width: 500px; margin: 0 auto; }
    .table-container { width: 100%; overflow-x: auto; border: 1px solid #1ed7de44; border-radius: 8px; margin-bottom: 20px; background-color: #161b22; }
    table { width: 100%; border-collapse: collapse; }
    th { position: sticky; top: 0; z-index: 100; background-color: #1f2937 !important; color: #1ed7de !important; padding: 12px; border: 1px solid #374151; }
    td { padding: 12px; border: 1px solid #374151; text-align: center !important; }
    
    div.stButton > button { 
        background-color: transparent !important; 
        color: #1ed7de !important; 
        border: 1px solid #1ed7de !important; 
        font-weight: bold !important; 
        transition: 0.3s; 
        width: 100%; 
    }
    div.stButton > button:hover { 
        background-color: #1ed7de22 !important; 
    }

    .header-container { display: flex; align-items: center; justify-content: flex-start; gap: 15px; margin: 25px 0; }
    .header-title { color: white !important; font-size: 2rem; font-weight: bold; margin: 0; line-height: 1; }
    .leyenda-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 10px; background: #161b22; padding: 15px; border-radius: 8px; border: 1px solid #1ed7de44; }
    .leyenda-item { display: flex; align-items: center; gap: 10px; font-size: 0.85rem; color: #e5e7eb; }
    .color-box { width: 14px; height: 14px; border-radius: 3px; flex-shrink: 0; }

    .top-pick-card {
        background: #1f2937;
        border: 1px solid #1ed7de44;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 15px;
        transition: transform 0.2s;
    }
    .top-pick-card:hover { border-color: #1ed7de; transform: translateY(-3px); }
    .card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }
    .card-fiabilidad { font-size: 0.7rem; font-weight: bold; padding: 2px 8px; border-radius: 4px; border: 1px solid; }
    .card-name { font-size: 1.1rem; font-weight: bold; color: white; margin: 5px 0; }
    .card-team { font-size: 0.8rem; color: #1ed7de; }
    .card-stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 12px; padding-top: 10px; border-top: 1px solid #374151; }
    .card-stat-item { text-align: center; }
    .card-stat-val { font-size: 1.1rem; font-weight: bold; color: #e5e7eb; display: block; margin-bottom: 4px; }
    .card-stat-lbl { font-size: 0.65rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# ESTRUCTURA DE LA APP
# ────────────────────────────────────────────────
st.markdown('<div class="main-logo-container"><img src="https://i.postimg.cc/SKPzCcyV/33.png" class="main-logo-img"></div>', unsafe_allow_html=True)

if "liga_sel" not in st.session_state: st.session_state.liga_sel = None
if "vista_activa" not in st.session_state: st.session_state.vista_activa = None
if "menu_op" not in st.session_state: st.session_state.menu_op = False
if "h2h_op" not in st.session_state: st.session_state.h2h_op = False
if "conf_op" not in st.session_state: st.session_state.conf_op = False
if "num_jugadores_mostrados" not in st.session_state: st.session_state.num_jugadores_mostrados = 10

if st.button("COMPETENCIAS", use_container_width=True):
    st.session_state.menu_op = not st.session_state.menu_op

if st.session_state.menu_op:
    sel = st.selectbox("Ligas", ["Selecciona Liga/Competencia"] + LIGAS_LISTA, label_visibility="collapsed")
    if sel != "Selecciona Liga/Competencia":
        st.session_state.liga_sel = sel
        st.session_state.menu_op = False
        st.session_state.vista_activa = "clas"
        st.rerun()

if st.session_state.liga_sel:
    liga = st.session_state.liga_sel
    st.markdown(f'<div class="header-container"><img src="{BANDERAS.get(liga, "")}" style="width:40px; height:auto;"><span class="header-title">{liga}</span></div>', unsafe_allow_html=True)
    
    v_act = st.session_state.vista_activa
    st.markdown(f"""
        <style>
        div.stButton > button:has(div:contains("{'Clasificación' if v_act=='clas' else 'NONE'}")),
        div.stButton > button:has(div:contains("{'Stats Equipos' if v_act=='stats' else 'NONE'}")),
        div.stButton > button:has(div:contains("{'Análisis Jugadores' if v_act=='players' else 'NONE'}")),
        div.stButton > button:has(div:contains("{'Ver Fixture' if v_act=='fix' else 'NONE'}")),
        div.stButton > button:has(div:contains("{'Picks & Cuotas' if v_act=='odds' else 'NONE'}")) {{
            background-color: #1ed7de !important;
            color: #0e1117 !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    cols = st.columns(5)
    labels = ["Clasificación", "Stats Equipos", "Análisis Jugadores", "Ver Fixture", "Picks & Cuotas"]
    keys = ["clas", "stats", "players", "fix", "odds"]
    
    for i, label in enumerate(labels):
        if cols[i].button(label, use_container_width=True):
            st.session_state.vista_activa = keys[i] if st.session_state.vista_activa != keys[i] else None
            st.session_state.num_jugadores_mostrados = 10
            st.rerun()

    st.divider()

    view = st.session_state.vista_activa
    if view:
        sufijo = MAPEO_ARCHIVOS.get(liga)
        df_clas_base = cargar_excel(f"CLASIFICACION_LIGA_{sufijo}.xlsx", "clasificacion")
        df_stats_base = cargar_excel(f"RESUMEN_STATS_{sufijo}.xlsx", "stats")

        if view == "players":
            st.markdown(f"#### 👤 Rendimiento Individual - {liga}")
            
            # --- SECCIÓN TOP PICKS CON CONFIANZA ---
            df_picks = cargar_excel("picks_finales_fiables.xlsx")
            if df_picks is not None:
                df_picks = df_picks.dropna(subset=['Jugador', 'Equipo'])
                df_picks = df_picks[(df_picks['Jugador'].astype(str).str.lower() != 'nan') & (df_picks['Equipo'].astype(str).str.lower() != 'nan')]
                
                df_liga_picks = df_picks[df_picks['Liga'] == sufijo].copy()
                df_liga_picks = df_liga_picks.sort_values(by='Score_Pick', ascending=False)
                df_liga_picks = df_liga_picks.drop_duplicates(subset=['Jugador'], keep='first')
                
                top_6 = df_liga_picks.head(6)
                if not top_6.empty:
                    st.markdown("##### 🔥 TOP PICKS DE ÉLITE (Algoritmo IA)")
                    p_cols = st.columns(3)
                    for idx, row in top_6.reset_index(drop=True).iterrows():
                        conf_vis = min(float(row['Score_Pick']), 100.0)
                        
                        # ASIGNACIÓN DE COLORES ACTUALIZADA (SEMÁFORO)
                        fiab_str = str(row['Fiabilidad']).upper()
                        if "ALTA" in fiab_str:
                            color_f = "#39FF14" # Verde Neón para Alta
                        elif "MEDIA" in fiab_str:
                            color_f = "#FFFF00" # Amarillo Neón para Media
                        elif "BAJA" in fiab_str:
                            color_f = "#FF3131" # Rojo Neón para Baja
                        else:
                            color_f = "#9ca3af"

                        with p_cols[idx % 3]:
                            st.markdown(f"""
                            <div class="top-pick-card">
                                <div class="card-header">
                                    <span class="card-fiabilidad" style="color:{color_f}; border-color:{color_f}77;">{row['Fiabilidad']}</span>
                                    <span style="font-size:0.7rem; color:#9ca3af;">PROYECCIÓN POR PARTIDO</span>
                                </div>
                                <div class="card-name">{row['Jugador']}</div>
                                <div class="card-team">{row['Equipo']}</div>
                                <div class="card-stats-grid">
                                    <div class="card-stat-item">
                                        <span class="card-stat-val">{row['Faltas_90']:.2f}</span>
                                        <span class="card-stat-lbl">Faltas</span>
                                    </div>
                                    <div class="card-stat-item">
                                        <span class="card-stat-val">{row['Tiros_90']:.2f}</span>
                                        <div style="display: flex; flex-direction: column; align-items: center; gap: 4px;">
                                            <img src="https://i.postimg.cc/8cpyfzqN/3131.png" width="45" height="45" style="margin-bottom: 2px;">
                                            <span class="card-stat-lbl">Tiros</span>
                                        </div>
                                    </div>
                                    <div class="card-stat-item">
                                        <span class="card-stat-val" style="color:#b59410;">{conf_vis:.1f}%</span>
                                        <span class="card-stat-lbl">Confianza</span>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # LEYENDA ACTUALIZADA CON COLORES SEMÁFORO
                    st.markdown("""
                    <div class="leyenda-grid" style="margin-bottom:25px;">
                        <div class="leyenda-item">
                            <span style="color:#b59410; font-weight:bold; font-size:1.1rem;">% Confianza:</span>
                            <span>Muestra la probabilidad de éxito basándose en la regularidad del jugador en sus últimos partidos.</span>
                        </div>
                        <div class="leyenda-item">
                            <span style="color:#1ed7de; font-weight:bold; font-size:1.1rem;">Fiabilidad:</span>
                            <span>Indica la solidez del pick según el histórico de minutos jugados; a mayor fiabilidad, más estable es el dato. 
                            <span style="color:#FF3131; font-weight:bold;">Baja</span> - 
                            <span style="color:#FFFF00; font-weight:bold;">Media</span> - 
                            <span style="color:#39FF14; font-weight:bold;">Alta</span></span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # --- TABLAS DE JUGADORES ---
            df_p = cargar_excel(f"SUPER_STATS_{sufijo}.xlsx", "general")
            if df_p is not None:
                if 'Pos' in df_p.columns:
                    df_p['Pos'] = df_p['Pos'].replace(MAPEO_POSICIONES)
                if 'Squad' in df_p.columns:
                    df_p['Squad'] = df_p['Squad'].apply(limpiar_nombre_equipo)
                
                f_col1, f_col2, f_col4 = st.columns([2, 2, 2])
                with f_col1:
                    eq_list = ["Todos"] + sorted(df_p['Squad'].unique().tolist())
                    eq_f = st.selectbox("Filtrar por Equipo", eq_list)
                with f_col2:
                    p_sel = st.multiselect("Posiciones", df_p['Pos'].unique(), default=df_p['Pos'].unique())
                with f_col4:
                    p_busq = st.text_input("🔍 Buscar Jugador", "").strip().lower()
                
                mask = (df_p['Pos'].isin(p_sel))
                if eq_f != "Todos": mask = mask & (df_p['Squad'] == eq_f)
                if p_busq: mask = mask & (df_p['Player'].str.lower().str.contains(p_busq))
                df_f = df_p[mask].copy()

                t1, t2 = st.tabs(["🎯 ATAQUE & REMATES", "🛡️ DISCIPLINA"])
                
                with t1:
                    c_atk = ['Player', 'Squad', 'Gls', 'Ast', 'Sh', 'SoT']
                    df_t1 = df_f[c_atk].sort_values(by='Gls', ascending=False)
                    df_t1_view = df_t1.head(st.session_state.num_jugadores_mostrados)
                    st.markdown(f'<div class="table-container">{df_t1_view.rename(columns=TRADUCCIONES).style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)
                    if len(df_t1) > st.session_state.num_jugadores_mostrados:
                        if st.button("Ver más jugadores (Ataque)", key="btn_atk"):
                            st.session_state.num_jugadores_mostrados += 10
                            st.rerun()

                with t2:
                    c_disc = ['Player', 'Squad', 'Fls', 'Fld', 'CrdY', 'CrdR']
                    df_t2 = df_f[c_disc].sort_values(by='Fls', ascending=False)
                    df_t2_view = df_t2.head(st.session_state.num_jugadores_mostrados)
                    st.markdown(f'<div class="table-container">{df_t2_view.rename(columns=TRADUCCIONES).style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)
                    if len(df_t2) > st.session_state.num_jugadores_mostrados:
                        if st.button("Ver más jugadores (Disciplina)", key="btn_disc"):
                            st.session_state.num_jugadores_mostrados += 10
                            st.rerun()
            else: st.info("ℹ️ Datos de jugadores no disponibles.")

        elif view == "odds":
            if st.button("⚔️ COMPARADOR H2H", use_container_width=True):
                st.session_state.h2h_op = not st.session_state.h2h_op
            if st.session_state.h2h_op and df_clas_base is not None and df_stats_base is not None:
                equipos = sorted(df_clas_base['EQUIPO'].unique())
                f1, f2, f3 = st.columns([2, 2, 1])
                eq_l = f1.selectbox("Equipo Local", equipos, index=0)
                eq_v = f2.selectbox("Equipo Visitante", equipos, index=min(1, len(equipos)-1))
                tipo_filtro = f3.selectbox("Filtro Stats", ["Global", "Local vs Visitante"])
                try:
                    d_l, d_v = df_clas_base[df_clas_base['EQUIPO'] == eq_l].iloc[0], df_clas_base[df_clas_base['EQUIPO'] == eq_v].iloc[0]
                    s_l, s_v = df_stats_base[df_stats_base['EQUIPO'] == eq_l].iloc[0], df_stats_base[df_stats_base['EQUIPO'] == eq_v].iloc[0]
                    radar_labels = ["PTS", "POSS", "GF", "xG", "VICT"]
                    radar_l = [min(d_l['PTS']*1.5, 100), float(s_l['Poss_num']), min(d_l['GF']*1.2, 100), min(float(s_l['xG_val'])*20, 100), min(d_l['G']*5, 100)]
                    radar_v = [min(d_v['PTS']*1.5, 100), float(s_v['Poss_num']), min(d_v['GF']*1.2, 100), min(float(s_v['xG_val'])*20, 100), min(d_v['G']*5, 100)]
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.markdown(generar_radar_svg(radar_l, radar_v, radar_labels), unsafe_allow_html=True)
                        st.markdown(f'<div style="text-align:center; font-size:10px;"><span style="color:#1ed7de">■ {eq_l}</span> <span style="color:#b59410">■ {eq_v}</span></div>', unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"""<div style="background:#1f2937; padding:15px; border-radius:12px; border:1px solid #1ed7de44;"><div style="display:flex; justify-content:space-between; border-bottom:1px solid #2d3139; padding:8px 0;"><span style="color:#1ed7de; font-weight:bold;">{d_l['PTS']}</span><span style="color:#9ca3af; font-size:0.8rem;">PUNTOS</span><span style="color:#1ed7de; font-weight:bold;">{d_v['PTS']}</span></div><div style="display:flex; justify-content:space-between; border-bottom:1px solid #2d3139; padding:8px 0;"><span>{d_l['G']}</span><span style="color:#9ca3af; font-size:0.8rem;">VICTORIAS</span><span>{d_v['G']}</span></div><div style="display:flex; justify-content:space-between; border-bottom:1px solid #2d3139; padding:8px 0;"><span>{s_l['xG_val']:.1f}</span><span style="color:#9ca3af; font-size:0.8rem;">xG</span><span>{s_v['xG_val']:.1f}</span></div><div style="margin-top:15px; display:flex; justify-content:space-between;">{grafico_picos_forma(d_l['ÚLTIMOS 5'], "left")}<span style="color:#9ca3af; font-size:0.8rem;">FORMA</span>{grafico_picos_forma(d_v['ÚLTIMOS 5'], "right")}</div></div>""", unsafe_allow_html=True)
                except: st.warning("Faltan datos para la comparativa.")
                st.divider()

            if st.button("🎯 ÍNDICE DE CONFIANZA", use_container_width=True):
                st.session_state.conf_op = not st.session_state.conf_op
            if st.session_state.conf_op and df_clas_base is not None and df_stats_base is not None:
                equipos = sorted(df_clas_base['EQUIPO'].unique())
                eq_sel = st.selectbox("Selecciona equipo", equipos)
                try:
                    s_r, c_r = df_stats_base[df_stats_base['EQUIPO']==eq_sel].iloc[0], df_clas_base[df_clas_base['EQUIPO']==eq_sel].iloc[0]
                    score = (float(s_r['xG_val']) * 0.4) + (float(c_r['PTS'])/(c_r['PJ'] or 1) * 15) + (str(c_r['ÚLTIMOS 5']).count('W') * 5)
                    perc = min(int(score * 2), 100)
                    st.markdown(f"""
                    <div style="background:#161b22; padding:20px; border-radius:12px; border:1px solid #1ed7de;">
                        <h4 style="color:#1ed7de; margin-top:0;">{eq_sel} - Reporte de Confianza</h4>
                        <div style="display:flex; align-items:center; gap:15px; margin:15px 0;">
                            <div style="flex:1; background:#2d3139; height:12px; border-radius:6px; overflow:hidden;">
                                <div style="width:{perc}%; background:#1ed7de; height:100%;"></div>
                            </div>
                            <span style="font-weight:bold; color:#1ed7de;">{perc}%</span>
                        </div>
                        <p style="font-size:0.9rem; color:#9ca3af; margin:0;"><b>Factor xG:</b> {s_r['xG_val']:.1f} | <b>Puntos/PJ:</b> {(c_r['PTS']/c_r['PJ']):.2f}</p>
                    </div>
                    """, unsafe_allow_html=True)
                except: st.error("No se pudo calcular.")
                st.divider()

            st.subheader("📊 Picks & Cuotas")
            raw = obtener_cuotas_api(liga)
            df_odds = procesar_cuotas(raw, df_clas_base)
            if df_odds is not None and not df_odds.empty:
                if df_stats_base is not None:
                    def predecir_goles(r):
                        try:
                            xg_l = df_stats_base[df_stats_base['EQUIPO'] == r['LOCAL']]['xG_val'].values[0]
                            xg_v = df_stats_base[df_stats_base['EQUIPO'] == r['VISITANTE']]['xG_val'].values[0]
                            return "🔥 Over" if (float(xg_l) + float(xg_v)) > 2.7 else "🛡️ Under"
                        except: return "---"
                    df_odds['TENDENCIA'] = df_odds.apply(predecir_goles, axis=1)
                def aplicar_estilo(row):
                    m = min(row['1'], row['X'], row['2'])
                    row['1'] = badge_cuota(row['1'], row['1']==m, row['VAL_H'])
                    row['X'] = badge_cuota(row['X'], row['X']==m)
                    row['2'] = badge_cuota(row['2'], row['2']==m)
                    return row
                styler_df = df_odds.apply(aplicar_estilo, axis=1)
                html = styler_df[['FECHA','LOCAL','VISITANTE','1','X','2','TENDENCIA']].style.hide(axis="index").to_html(escape=False)
                st.markdown(f'<div class="table-container">{html}</div>', unsafe_allow_html=True)
                st.markdown("""<div class="leyenda-grid"><div class="leyenda-item"><div class="color-box" style="background:#b59410;"></div><span><b>Value Bet (⭐):</b> Valor Estadístico.</span></div><div class="leyenda-item"><div class="color-box" style="background:#137031;"></div><span><b>Favorito:</b> Más probable.</span></div><div class="leyenda-item"><span style="color:#1ed7de; font-weight:bold;">🔥 Over:</span><span>+2.5 Goles.</span></div><div class="leyenda-item"><span style="color:#9ca3af; font-weight:bold;">🛡️ Under:</span><span>-2.5 Goles.</span></div></div>""", unsafe_allow_html=True)

        else:
            # SECCIÓN STATS EQUIPOS (ORIGINAL CON INTEGRACIÓN DE SCRAPEO)
            configs = {"clas": (f"CLASIFICACION_LIGA_{sufijo}.xlsx", "clasificacion"), "stats": (f"RESUMEN_STATS_{sufijo}.xlsx", "stats"), "fix": (f"CARTELERA_PROXIMOS_{sufijo}.xlsx", "fixture")}
            archivo, tipo = configs[view]
            df = cargar_excel(archivo, tipo=tipo)
            if df is not None:
                if 'ÚLTIMOS 5' in df.columns: df['ÚLTIMOS 5'] = df['ÚLTIMOS 5'].apply(formatear_last_5)
                cols_to_drop = ['xG_val', 'Poss_num']
                df_view = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
                
                # FILTRO DUAL MEJORADO (SIN TOCAR ESTÉTICA)
                lista_equipos = sorted(df['EQUIPO'].unique().tolist()) if 'EQUIPO' in df.columns else []
                f1, f2 = st.columns([1, 1])
                with f1:
                    busqueda = st.text_input("🔍 Escribir equipo...", "").strip().lower()
                with f2:
                    seleccion_lista = st.selectbox("📋 O selecciona de la lista:", [""] + lista_equipos)
                
                equipo_final = seleccion_lista if seleccion_lista else busqueda
                
                if equipo_final and 'EQUIPO' in df_view.columns: 
                    df_view = df_view[df_view['EQUIPO'].str.lower().str.contains(equipo_final.lower())]
                
                styler = df_view.style.hide(axis="index")
                if 'PTS' in df_view.columns: styler = styler.set_properties(subset=['PTS'], **{'background-color': '#1ed7de22', 'font-weight': 'bold', 'color': '#1ed7de'})
                st.markdown(f'<div class="table-container">{styler.to_html(escape=False)}</div>', unsafe_allow_html=True)

                # INTEGRACIÓN DEL EXCEL DE JUGADORES (SCRAPEO)
                if equipo_final:
                    st.markdown(f"#### 🏟️ Plantilla y Stats Individuales")
                    df_jug = cargar_excel("jugadoreswhoscored.csv") # Scrapeo desde github
                    if df_jug is not None:
                        # Limpieza de nombre: Quita números al final
                        df_jug['Jugador'] = df_jug['Jugador'].str.replace(r'\d+$', '', regex=True)
                        
                        # Filtrar por equipo y liga
                        df_res = df_jug[
                            (df_jug['Equipo'].str.lower().str.contains(equipo_final.lower())) & 
                            (df_jug['Liga'] == liga)
                        ]
                        
                        if not df_res.empty:
                            # Diccionario de usuario/apostador para las columnas del scrapeo
                            mapeo_scrapeo = {
                                'Jugador': 'JUGADOR', 'Mins': '⏱️ MIN', 'Rating': '⭐ RATING',
                                'Amarillas': '🟨', 'Rojas': '🟥', 'Entradas_Std': '🛡️ ENTRADAS',
                                'Regates_p90': '⚡ REG(p90)', 'Goles': '⚽ GOLES', 'Asistencias': '🅰️ ASIST',
                                'Pases Clave': '🔑 P.CLAVE', 'Tiros_Arco_p90': '🎯 TIROS(p90)', 'Faltas recibidas': '🤕 F.REC'
                            }
                            cols_mostrar = [c for c in mapeo_scrapeo.keys() if c in df_res.columns]
                            df_final_jug = df_res[cols_mostrar].rename(columns=mapeo_scrapeo)
                            
                            # Mostramos con tu tabla característica
                            st.markdown(f'<div class="table-container">{df_final_jug.style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

st.write("---")
st.caption("InsideBet Official | scrapeo")
