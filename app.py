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
        # Limpieza profunda para asegurar solo el número
        if isinstance(valor, str):
            num_clean = "".join(filter(lambda x: x.isdigit() or x == '.', valor))
            num = float(num_clean) if num_clean else 0
        else:
            num = float(valor)
        percent = min(max(int(num), 0), 100)
        return f'''
        <div style="position: relative; width: 100px; background-color: #2d3139; border-radius: 4px; height: 18px; overflow: hidden; border: 1px solid #4b5563; margin: 0 auto;">
            <div style="width: {percent}%; background-color: #1ed7de; height: 100%;"></div>
            <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: white; font-size: 10px; font-weight: bold; text-shadow: 1px 1px 1px black;">
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

@st.cache_data(ttl=300)
def cargar_excel(ruta_archivo, tipo="general"):
    url = f"{BASE_URL}/{ruta_archivo}"
    try:
        df = pd.read_excel(url)
        if tipo == "stats":
            if 'Squad' in df.columns:
                df['Squad'] = df['Squad'].apply(limpiar_nombre_equipo)
            if len(df.columns) >= 17:
                df = df.rename(columns={df.columns[16]: 'xG'})
            
            # Formatear columnas ANTES de renombrar a TRADUCCIONES
            if 'xG' in df.columns: df['xG'] = df['xG'].apply(formatear_xg_badge)
            if 'Poss' in df.columns: df['Poss'] = df['Poss'].apply(html_barra_posesion)
            
            cols_ok = ['Squad', 'MP', 'Poss', 'Gls', 'Ast', 'CrdY', 'CrdR', 'xG']
            df = df[[c for c in cols_ok if c in df.columns]]
            df = df.rename(columns=TRADUCCIONES)
        
        elif tipo == "clasificacion":
            if 'Squad' in df.columns:
                df['Squad'] = df['Squad'].apply(limpiar_nombre_equipo)
            df = df.rename(columns=TRADUCCIONES)
            cols_ver = ['POS', 'EQUIPO', 'PTS', 'PJ', 'G', 'E', 'P', 'GF', 'GC', 'DG', 'ÚLTIMOS 5']
            df = df[[c for c in cols_ver if c in df.columns]]
                
        elif tipo == "fixture":
            df = df.rename(columns=TRADUCCIONES)
            if 'LOCAL' in df.columns: df['LOCAL'] = df['LOCAL'].apply(limpiar_nombre_equipo)
            if 'VISITANTE' in df.columns: df['VISITANTE'] = df['VISITANTE'].apply(limpiar_nombre_equipo)
            if 'FECHA' in df.columns: df['FECHA'] = df['FECHA'].apply(lambda x: str(x).split(' ')[0] if pd.notna(x) else "TBD")
        
        return df.dropna(how='all').reset_index(drop=True)
    except: return None

# ────────────────────────────────────────────────
# CUOTAS Y LÓGICA
# ────────────────────────────────────────────────

def obtener_cuotas_api(liga_nombre):
    sport_key = MAPEO_ODDS_API.get(liga_nombre)
    if not sport_key or not API_KEY: return None
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
    params = {'apiKey': API_KEY, 'regions': 'eu', 'markets': 'h2h', 'oddsFormat': 'decimal'}
    try:
        r = requests.get(url, params=params)
        return r.json()
    except: return None

def badge_cuota(val, es_minimo=False, tiene_valor=False):
    color_bg = "#b59410" if tiene_valor else ("#137031" if es_minimo else "#2d3139")
    color_text = "white" if tiene_valor else ("#00ff88" if es_minimo else "#ced4da")
    return f'<div style="display: flex; justify-content: center;"><span style="background-color: {color_bg}; color: {color_text}; padding: 5px 12px; border-radius: 6px; font-weight: bold; font-size: 13px; min-width: 60px; text-align: center; border: 1px solid #4b5563;">{val:.2f}</span></div>'

# ────────────────────────────────────────────────
# ESTILOS CSS
# ────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e5e7eb; }
    .main-logo-container { text-align: center; padding: 20px 0; }
    .main-logo-img { width: 50%; max-width: 500px; }
    .table-container { width: 100%; overflow-x: auto; border: 1px solid #1ed7de44; border-radius: 8px; margin-bottom: 50px; background-color: #161b22; }
    table { width: 100%; border-collapse: collapse; }
    th { position: sticky; top: 0; background-color: #1f2937 !important; color: #1ed7de !important; padding: 12px; border: 1px solid #374151; font-size: 0.85rem; }
    td { padding: 12px; border: 1px solid #374151; text-align: center !important; }
    .header-container { display: flex; align-items: center; gap: 15px; margin: 25px 0; }
    .header-title { color: white !important; font-size: 2rem; font-weight: bold; margin: 0; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# ESTRUCTURA DE LA APP
# ────────────────────────────────────────────────

st.markdown('<div class="main-logo-container"><img src="https://i.postimg.cc/SKPzCcyV/33.png" class="main-logo-img"></div>', unsafe_allow_html=True)

if "liga_sel" not in st.session_state: st.session_state.liga_sel = None
if "vista_activa" not in st.session_state: st.session_state.vista_activa = None

if st.button("COMPETENCIAS", use_container_width=True):
    st.session_state.menu_op = not st.session_state.get('menu_op', False)

if st.session_state.get('menu_op', False):
    sel = st.selectbox("Ligas", ["Selecciona Liga/Competencia"] + LIGAS_LISTA, label_visibility="collapsed")
    if sel != "Selecciona Liga/Competencia":
        st.session_state.liga_sel = sel
        st.session_state.menu_op = False
        st.session_state.vista_activa = "clas"
        st.rerun()

if st.session_state.liga_sel:
    liga = st.session_state.liga_sel
    st.markdown(f'<div class="header-container"><img src="{BANDERAS.get(liga, "")}" style="width:40px;"><span class="header-title">{liga}</span></div>', unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("Clasificación", use_container_width=True): st.session_state.vista_activa = "clas"; st.rerun()
    if c2.button("Stats Generales", use_container_width=True): st.session_state.vista_activa = "stats"; st.rerun()
    if c3.button("Ver Fixture", use_container_width=True): st.session_state.vista_activa = "fix"; st.rerun()
    if c4.button("Picks & Cuotas", use_container_width=True): st.session_state.vista_activa = "odds"; st.rerun()

    view = st.session_state.vista_activa
    if view:
        sufijo = MAPEO_ARCHIVOS.get(liga)
        df_clas = cargar_excel(f"CLASIFICACION_LIGA_{sufijo}.xlsx", "clasificacion")
        df_stats = cargar_excel(f"RESUMEN_STATS_{sufijo}.xlsx", "stats")

        if view == "odds":
            st.subheader("⚔️ Comparador H2H")
            if df_clas is not None and df_stats is not None:
                equipos = sorted(df_clas['EQUIPO'].unique())
                col_h1, col_h2 = st.columns(2)
                eq_l = col_h1.selectbox("Local", equipos, index=0)
                eq_v = col_h2.selectbox("Visitante", equipos, index=min(1, len(equipos)-1))
                
                try:
                    d_l = df_clas[df_clas['EQUIPO'] == eq_l].iloc[0]
                    d_v = df_clas[df_clas['EQUIPO'] == eq_v].iloc[0]
                    s_l = df_stats[df_stats['EQUIPO'] == eq_l].iloc[0]
                    s_v = df_stats[df_stats['EQUIPO'] == eq_v].iloc[0]
                    
                    def row_h2h(label, val1, val2, highlight=False):
                        color = "#1ed7de" if highlight else "white"
                        return f"""<div style="display: flex; justify-content: space-between; border-bottom: 1px solid #2d3139; padding: 10px 0;">
                            <span style="font-weight: bold; color: {color}; width: 25%; text-align: left;">{val1}</span>
                            <span style="color: #9ca3af; font-size: 0.8rem; text-align: center;">{label.upper()}</span>
                            <span style="font-weight: bold; color: {color}; width: 25%; text-align: right;">{val2}</span>
                        </div>"""

                    # Limpieza para H2H (extraer % del HTML de la barra)
                    p_l = re.findall(r"\d+%", str(s_l['POSESIÓN']))[0] if '%' in str(s_l['POSESIÓN']) else "0%"
                    p_v = re.findall(r"\d+%", str(s_v['POSESIÓN']))[0] if '%' in str(s_v['POSESIÓN']) else "0%"
                    xg_l = str(s_l['xG']).split('+')[-1].split('<')[0]
                    xg_v = str(s_v['xG']).split('+')[-1].split('<')[0]

                    st.markdown(f"""
                    <div style="background: #1f2937; padding: 25px; border-radius: 12px; border: 1px solid #1ed7de44;">
                        {row_h2h("Puntos", d_l['PTS'], d_v['PTS'], True)}
                        {row_h2h("Victorias", d_l['G'], d_v['G'])}
                        {row_h2h("Goles Favor", d_l['GF'], d_v['GF'])}
                        {row_h2h("xG Generado", xg_l, xg_v)}
                        {row_h2h("Posesión", p_l, p_v)}
                        <div style="margin-top: 15px; display: flex; justify-content: space-between; align-items: center; padding-top: 10px;">
                            <div style="width: 40%">{formatear_last_5(d_l['ÚLTIMOS 5'])}</div>
                            <span style="color: #9ca3af; font-size: 0.8rem;">FORMA</span>
                            <div style="width: 40%; display: flex; justify-content: flex-end;">{formatear_last_5(d_v['ÚLTIMOS 5'])}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                except: st.error("Error al cruzar datos de equipos.")

        else:
            configs = {"clas": (df_clas, "ÚLTIMOS 5"), "stats": (df_stats, None), "fix": (cargar_excel(f"CARTELERA_PROXIMOS_{sufijo}.xlsx", "fixture"), None)}
            df_view, col_f = configs[view]
            if df_view is not None:
                if col_f and col_f in df_view.columns: df_view[col_f] = df_view[col_f].apply(formatear_last_5)
                html = df_view.style.hide(axis="index").to_html(escape=False)
                st.markdown(f'<div class="table-container">{html}</div>', unsafe_allow_html=True)

st.write("---")
st.caption("InsideBet Official | scrapeo")
