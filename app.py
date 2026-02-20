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
        return f'<div class="bar-container"><div class="bar-bg"><div class="bar-fill" style="width: {percent}%;"></div></div><div class="bar-text">{percent}%</div></div>'
    except: return valor

def formatear_last_5(valor):
    if pd.isna(valor): return ""
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
        if 'Home' in df.columns and 'Away' in df.columns:
            df = df.dropna(subset=['Home', 'Away'], how='all')

        if tipo == "stats":
            if 'Squad' in df.columns:
                df['Squad'] = df['Squad'].apply(limpiar_nombre_equipo)
            if len(df.columns) >= 17:
                df = df.rename(columns={df.columns[16]: 'xG'})
            df['xG_val'] = df['xG'].fillna(0)
            if 'xG' in df.columns: df['xG'] = df['xG'].apply(formatear_xg_badge)
            if 'Poss' in df.columns: df['Poss'] = df['Poss'].apply(html_barra_posesion)
            cols_ok = ['Squad', 'MP', 'Poss', 'Gls', 'Ast', 'CrdY', 'CrdR', 'xG', 'xG_val']
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
    
    .main-logo-container {
        text-align: center;
        width: 100%;
        padding: 20px 0;
    }
    .main-logo-img {
        width: 50%;
        max-width: 500px;
        margin: 0 auto;
    }

    .table-container { 
        width: 100%; 
        overflow-x: auto; 
        border: 1px solid #1ed7de44; 
        border-radius: 8px; 
        margin-bottom: 50px;
        background-color: #161b22;
    }
    table { width: 100%; border-collapse: collapse; }
    th { 
        position: sticky; top: 0; z-index: 100;
        background-color: #1f2937 !important; color: #1ed7de !important; 
        padding: 12px; border: 1px solid #374151; 
    }
    td { padding: 12px; border: 1px solid #374151; text-align: center !important; }

    div.stButton > button { 
        background-color: transparent !important; 
        color: #1ed7de !important; 
        border: 1px solid #1ed7de !important;
        font-weight: bold !important;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #1ed7de22 !important;
    }

    .stButton > button[kind="secondary"]:first-child { 
        background-color: #1ed7de !important; 
        color: #0e1117 !important; 
        border: none !important;
    }

    div[data-baseweb="select"] {
        border: 1px solid #1ed7de !important;
    }

    .header-container {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        gap: 15px;
        margin: 25px 0;
    }
    .header-title { color: white !important; font-size: 2rem; font-weight: bold; margin: 0; line-height: 1; }

    .bar-fill { background-color: #1ed7de; height: 100%; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# ESTRUCTURA DE LA APP
# ────────────────────────────────────────────────

st.markdown("""
    <div class="main-logo-container">
        <img src="https://i.postimg.cc/SKPzCcyV/33.png" class="main-logo-img">
    </div>
    """, unsafe_allow_html=True)

if "liga_sel" not in st.session_state: st.session_state.liga_sel = None
if "vista_activa" not in st.session_state: st.session_state.vista_activa = None
if "menu_op" not in st.session_state: st.session_state.menu_op = False

# Botón principal
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
    st.markdown(f'''
        <div class="header-container">
            <img src="{BANDERAS.get(liga, "")}" style="width:40px; height:auto;">
            <span class="header-title">{liga}</span>
        </div>
    ''', unsafe_allow_html=True)
    
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

    st.divider()

    view = st.session_state.vista_activa
    if view:
        sufijo = MAPEO_ARCHIVOS.get(liga)
        df_clas_base = cargar_excel(f"CLASIFICACION_LIGA_{sufijo}.xlsx", "clasificacion")
        df_stats_base = cargar_excel(f"RESUMEN_STATS_{sufijo}.xlsx", "stats")

        if view == "odds":
            st.subheader("⚔️ Comparador H2H")
            if df_clas_base is not None and df_stats_base is not None:
                equipos = sorted(df_clas_base['EQUIPO'].unique())
                col_h1, col_h2 = st.columns(2)
                eq_l = col_h1.selectbox("Local", equipos, index=0)
                eq_v = col_h2.selectbox("Visitante", equipos, index=1)
                
                try:
                    # Datos de Clasificación
                    d_l = df_clas_base[df_clas_base['EQUIPO'] == eq_l].iloc[0]
                    d_v = df_clas_base[df_clas_base['EQUIPO'] == eq_v].iloc[0]
                    
                    # Datos de Stats
                    s_l = df_stats_base[df_stats_base['EQUIPO'] == eq_l].iloc[0]
                    s_v = df_stats_base[df_stats_base['EQUIPO'] == eq_v].iloc[0]
                    
                    def row_h2h(label, val1, val2, highlight=False):
                        color = "#1ed7de" if highlight else "white"
                        return f"""
                        <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #2d3139; padding: 10px 0;">
                            <span style="font-weight: bold; color: {color}; width: 20%; text-align: left;">{val1}</span>
                            <span style="color: #9ca3af; font-size: 0.85rem;">{label.upper()}</span>
                            <span style="font-weight: bold; color: {color}; width: 20%; text-align: right;">{val2}</span>
                        </div>"""

                    st.markdown(f"""
                    <div style="background: #1f2937; padding: 25px; border-radius: 12px; border: 1px solid #1ed7de44;">
                        {row_h2h("Puntos", d_l['PTS'], d_v['PTS'], True)}
                        {row_h2h("Victorias", d_l['G'], d_v['G'])}
                        {row_h2h("Goles Favor", d_l['GF'], d_v['GF'])}
                        {row_h2h("xG Generado", s_l['xG_val'], s_v['xG_val'])}
                        {row_h2h("Posesión Prom.", s_l['POSESIÓN'], s_v['POSESIÓN'])}
                        <div style="margin-top: 15px; display: flex; justify-content: space-between; align-items: center;">
                            <div style="width: 40%">{formatear_last_5(d_l.get('ÚLTIMOS 5', ''))}</div>
                            <span style="color: #9ca3af; font-size: 0.85rem;">FORMA</span>
                            <div style="width: 40%; display: flex; justify-content: flex-end;">{formatear_last_5(d_v.get('ÚLTIMOS 5', ''))}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.warning("Datos de comparación incompletos.")

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

        else:
            configs = {"clas": (f"CLASIFICACION_LIGA_{sufijo}.xlsx", "clasificacion"), 
                       "stats": (f"RESUMEN_STATS_{sufijo}.xlsx", "stats"), 
                       "fix": (f"CARTELERA_PROXIMOS_{sufijo}.xlsx", "fixture")}
            archivo, tipo = configs[view]
            df = cargar_excel(archivo, tipo=tipo)
            if df is not None:
                if 'ÚLTIMOS 5' in df.columns: df['ÚLTIMOS 5'] = df['ÚLTIMOS 5'].apply(formatear_last_5)
                if 'xG_val' in df.columns: df = df.drop(columns=['xG_val'])
                styler = df.style.hide(axis="index")
                if 'PTS' in df.columns: 
                    styler = styler.set_properties(subset=['PTS'], **{'background-color': '#1ed7de22', 'font-weight': 'bold', 'color': '#1ed7de'})
                st.markdown(f'<div class="table-container">{styler.to_html(escape=False)}</div>', unsafe_allow_html=True)

st.write("---")
st.caption("InsideBet Official | scrapeo")
