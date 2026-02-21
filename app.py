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

def generar_sparkline_score(score_actual):
    val2 = score_actual * 0.95
    val3 = score_actual * 0.90
    puntos = [val3, val2, score_actual]
    max_p = max(puntos) if max(puntos) > 0 else 1
    norm = [(p/max_p)*18 for p in puntos]
    svg = f'''
    <svg width="45" height="20" style="vertical-align: middle;">
        <polyline points="0,{20-norm[0]} 22,{20-norm[1]} 44,{20-norm[2]}" fill="none" stroke="#1ed7de" stroke-width="2" />
        <circle cx="44" cy="{20-norm[2]}" r="2" fill="#1ed7de" />
    </svg>
    '''
    return svg

def corregir_fiabilidad_contexto(row):
    try:
        mins = float(row.get('Minutos', 0))
        score = float(row.get('Score_Pick', 0))
        if mins < 300 and score > 50: return "RIESGO/RETORNO ⚠️", "#ff4b4b"
        if mins < 300: return "BAJA (Muestra) ⚠️", "#821f1f"
        if mins >= 450: return "ALTA 🔥", "#137031"
        return "MEDIA 📈", "#b59410"
    except: return "N/A", "#4b5563"

def formatear_xg_badge(val):
    try:
        num = float(val)
        color = "#137031" if num > 1.50 else "#821f1f"
        return f'<div style="display: flex; justify-content: center;"><span style="background-color: {color}; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 12px; min-width: 45px; text-align: center;">+{num:.1f}</span></div>'
    except: return val

def html_barra_posesion(valor):
    try:
        num = float(re.findall(r"[-+]?\d*\.\d+|\d+", str(valor))[0])
        percent = min(max(int(num), 0), 100)
        return f'''<div style="position: relative; width: 100%; background-color: #2d3139; border-radius: 4px; height: 20px; overflow: hidden; border: 1px solid #4b5563;"><div style="width: {percent}%; background-color: #1ed7de; height: 100%;"></div><div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: white; font-size: 11px; font-weight: bold; text-shadow: 1px 1px 2px black;">{percent}%</div></div>'''
    except: return valor

def grafico_picos_forma(valor, alineacion="left"):
    if pd.isna(valor) or valor == "": return ""
    letras = list(str(valor).upper().replace(" ", ""))[:5]
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
    return f'''<div style="width: 100%; height: 30px; display: flex; align-items: center; justify-content: {'flex-start' if alineacion=='left' else 'flex-end'};"><svg width="130" height="22" viewBox="0 0 130 22"><path d="{path_d}" fill="none" stroke="#1ed7de" stroke-width="1.2" opacity="0.4" />{''.join(puntos_svg)}</svg></div>'''

# ────────────────────────────────────────────────
# FUNCIONES DE CARGA
# ────────────────────────────────────────────────

@st.cache_data(ttl=300)
def cargar_excel(ruta_archivo, tipo="general"):
    url = f"{BASE_URL}/{ruta_archivo}" if "picks" in ruta_archivo else (f"{BASE_URL}/Estadisticas_Jugadores/{ruta_archivo}" if "SUPER" in ruta_archivo else f"{BASE_URL}/{ruta_archivo}")
    try:
        df = pd.read_excel(url)
        if tipo == "stats":
            if 'Squad' in df.columns: df['Squad'] = df['Squad'].apply(limpiar_nombre_equipo)
            if 'Poss' in df.columns:
                df['Poss_num'] = df['Poss'].apply(lambda x: re.findall(r"\d+", str(x))[0] if re.findall(r"\d+", str(x)) else "0")
                df['Poss'] = df['Poss'].apply(html_barra_posesion)
            if len(df.columns) >= 17: df['xG_val'] = df.iloc[:, 16].fillna(0)
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
    .main-logo-container { text-align: center; width: 100%; padding: 20px 0; }
    .main-logo-img { width: 50%; max-width: 500px; margin: 0 auto; }
    .table-container { width: 100%; overflow-x: auto; border: 1px solid #1ed7de44; border-radius: 8px; margin-bottom: 20px; background-color: #161b22; }
    th { background-color: #1f2937 !important; color: #1ed7de !important; padding: 12px; border: 1px solid #374151; }
    td { padding: 12px; border: 1px solid #374151; text-align: center !important; }
    div.stButton > button { background-color: transparent !important; color: #1ed7de !important; border: 1px solid #1ed7de !important; font-weight: bold !important; width: 100%; }
    .pick-card { background: #1f2937; border: 1px solid #1ed7de44; border-radius: 10px; padding: 15px; margin-bottom: 10px; }
    .leyenda-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; background: #161b22; padding: 15px; border-radius: 8px; border: 1px solid #1ed7de44; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# ESTRUCTURA DE LA APP
# ────────────────────────────────────────────────
st.markdown('<div class="main-logo-container"><img src="https://i.postimg.cc/SKPzCcyV/33.png" class="main-logo-img"></div>', unsafe_allow_html=True)

if "liga_sel" not in st.session_state: st.session_state.liga_sel = None
if "vista_activa" not in st.session_state: st.session_state.vista_activa = None
if "menu_op" not in st.session_state: st.session_state.menu_op = False
if "num_jugadores_mostrados" not in st.session_state: st.session_state.num_jugadores_mostrados = 10

if st.button("COMPETENCIAS", use_container_width=True):
    st.session_state.menu_op = not st.session_state.menu_op

if st.session_state.menu_op:
    sel = st.selectbox("Ligas", ["Selecciona Liga"] + LIGAS_LISTA, label_visibility="collapsed")
    if sel != "Selecciona Liga":
        st.session_state.liga_sel = sel
        st.session_state.menu_op = False
        st.session_state.vista_activa = "clas"
        st.rerun()

if st.session_state.liga_sel:
    liga = st.session_state.liga_sel
    st.markdown(f'<div style="display:flex; align-items:center; gap:15px; margin:20px 0;"><img src="{BANDERAS.get(liga)}" style="width:40px;"><h2>{liga}</h2></div>', unsafe_allow_html=True)
    
    v_act = st.session_state.vista_activa
    cols = st.columns(5)
    labels = ["Clasificación", "Stats Equipos", "Análisis Jugadores", "Ver Fixture", "Picks & Cuotas"]
    keys = ["clas", "stats", "players", "fix", "odds"]
    
    for i, label in enumerate(labels):
        if cols[i].button(label, use_container_width=True):
            st.session_state.vista_activa = keys[i]
            st.session_state.num_jugadores_mostrados = 10
            st.rerun()

    view = st.session_state.vista_activa
    sufijo = MAPEO_ARCHIVOS.get(liga)

    if view == "players":
        st.markdown("#### 👤 Rendimiento Individual")
        df_picks = cargar_excel("picks_finales_fiables.xlsx")
        if df_picks is not None:
            df_picks = df_picks.drop_duplicates(subset=['Jugador']).query("Jugador != 'Opponent Total'")
            df_p_liga = df_picks[df_picks['Liga'] == sufijo].head(6)
            if not df_p_liga.empty:
                st.markdown("##### 🔥 TOP PICKS ANALIZADOS")
                p_cols = st.columns(3)
                for i, (idx, row) in enumerate(df_p_liga.iterrows()):
                    label_f, color_f = corregir_fiabilidad_contexto(row)
                    spark = generar_sparkline_score(float(row['Score_Pick']))
                    with p_cols[i % 3]:
                        st.markdown(f'''<div class="pick-card"><div style="display:flex; justify-content:space-between;"><span style="background:{color_f}44; color:{color_f}; padding:2px 8px; border-radius:4px; font-size:10px; font-weight:bold;">{label_f}</span>{spark}</div><div style="color:white; font-weight:bold; font-size:16px; margin-top:8px;">{row['Jugador']}</div><div style="color:#9ca3af; font-size:12px;">{row['Equipo']}</div><div style="display:flex; justify-content:space-between; margin-top:10px; border-top:1px solid #374151; padding-top:8px;"><div style="text-align:center;"><div style="color:#1ed7de; font-weight:bold;">{row['Faltas_90']}</div><div style="font-size:9px;">FALTAS/90</div></div><div style="text-align:center;"><div style="color:#1ed7de; font-weight:bold;">{row['Tiros_90']}</div><div style="font-size:9px;">TIROS/90</div></div><div style="text-align:center;"><div style="color:#b59410; font-weight:bold;">{row['Score_Pick']}</div><div style="font-size:9px;">SCORE</div></div></div></div>''', unsafe_allow_html=True)

        df_p = cargar_excel(f"SUPER_STATS_{sufijo}.xlsx")
        if df_p is not None:
            if 'Pos' in df_p.columns: df_p['Pos'] = df_p['Pos'].replace(MAPEO_POSICIONES)
            if 'Squad' in df_p.columns: df_p['Squad'] = df_p['Squad'].apply(limpiar_nombre_equipo)
            
            c1, c2, c3 = st.columns(3)
            eq_f = c1.selectbox("Equipo", ["Todos"] + sorted(df_p['Squad'].unique().tolist()))
            pos_f = c2.multiselect("Posición", df_p['Pos'].unique(), default=df_p['Pos'].unique())
            busq = c3.text_input("🔍 Buscar", "").lower()
            
            mask = df_p['Pos'].isin(pos_f)
            if eq_f != "Todos": mask &= (df_p['Squad'] == eq_f)
            if busq: mask &= (df_p['Player'].str.lower().str.contains(busq))
            df_f = df_p[mask].copy()

            t1, t2 = st.tabs(["🎯 ATAQUE", "🛡️ DISCIPLINA"])
            with t1:
                df_t1 = df_f[['Player', 'Squad', 'Gls', 'Ast', 'Sh', 'SoT']].sort_values(by='Gls', ascending=False).head(st.session_state.num_jugadores_mostrados)
                st.markdown(f'<div class="table-container">{df_t1.rename(columns=TRADUCCIONES).style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)
            with t2:
                df_t2 = df_f[['Player', 'Squad', 'Fls', 'Fld', 'CrdY', 'CrdR']].sort_values(by='Fls', ascending=False).head(st.session_state.num_jugadores_mostrados)
                st.markdown(f'<div class="table-container">{df_t2.rename(columns=TRADUCCIONES).style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)
            
            if st.button("Ver más jugadores"):
                st.session_state.num_jugadores_mostrados += 10
                st.rerun()

    elif view == "clas":
        df = cargar_excel(f"CLASIFICACION_LIGA_{sufijo}.xlsx", "clasificacion")
        if df is not None:
            if 'ÚLTIMOS 5' in df.columns: df['ÚLTIMOS 5'] = df['ÚLTIMOS 5'].apply(lambda x: grafico_picos_forma(x))
            st.markdown(f'<div class="table-container">{df.style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

    elif view == "stats":
        df = cargar_excel(f"RESUMEN_STATS_{sufijo}.xlsx", "stats")
        if df is not None:
            cols_v = [c for c in df.columns if c not in ['Poss_num', 'xG_val']]
            st.markdown(f'<div class="table-container">{df[cols_v].style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

# Footer
st.markdown("<center><small>InsideBet 2026 | Datos: FBRef</small></center>", unsafe_allow_html=True)
