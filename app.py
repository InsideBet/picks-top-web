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
    'CrdY': 'AMARILLAS', 'CrdR': 'ROJAS', 'xG': 'xG'
}

# ────────────────────────────────────────────────
# FUNCIONES DE FORMATO
# ────────────────────────────────────────────────

def limpiar_nombre_equipo(nombre):
    if pd.isna(nombre): return nombre
    return re.sub(r'^[a-z]+\s+', '', str(nombre))

def formatear_equipo_con_logo(nombre, logo_url=None):
    if not logo_url or pd.isna(logo_url):
        logo_url = "https://i.postimg.cc/85zX8M6v/logo-placeholder.png"
    
    return f'''
    <div style="display: flex; align-items: center; gap: 10px;">
        <img src="{logo_url}" width="24" height="24" style="object-fit: contain;">
        <span>{nombre}</span>
    </div>
    '''

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
    url_mapeo = f"https://raw.githubusercontent.com/{USER}/{REPO}/main/mapeo_escudos.xlsx"
    
    try:
        df = pd.read_excel(url)
        
        try:
            df_mapeo = pd.read_excel(url_mapeo)
        except:
            df_mapeo = pd.DataFrame(columns=['EQUIPO', 'LOGO_URL'])

        col_equipo = 'Squad' if 'Squad' in df.columns else 'EQUIPO'
        
        if col_equipo in df.columns:
            df[col_equipo] = df[col_equipo].apply(limpiar_nombre_equipo)
            
            # Unimos con los escudos
            df = pd.merge(df, df_mapeo[['EQUIPO', 'LOGO_URL']], 
                          left_on=col_equipo, right_on='EQUIPO', 
                          how='left', suffixes=('', '_map'))
            
            # Formateamos HTML del equipo
            df[col_equipo] = df.apply(lambda row: formatear_equipo_con_logo(row[col_equipo], row['LOGO_URL']), axis=1)
            
            # Limpieza de columnas del merge
            if 'EQUIPO_map' in df.columns: df.drop(columns=['EQUIPO_map'], inplace=True)
            if 'LOGO_URL' in df.columns: df.drop(columns=['LOGO_URL'], inplace=True)

        if tipo == "stats":
            if len(df.columns) >= 17:
                df = df.rename(columns={df.columns[16]: 'xG'})
            df['xG_val'] = df['xG'].fillna(0)
            if 'xG' in df.columns: df['xG'] = df['xG'].apply(formatear_xg_badge)
            if 'Poss' in df.columns: df['Poss'] = df['Poss'].apply(html_barra_posesion)
            cols_ok = ['Squad', 'MP', 'Poss', 'Gls', 'Ast', 'CrdY', 'CrdR', 'xG', 'xG_val']
            df = df[[c for c in cols_ok if c in df.columns]]
            df = df.rename(columns=TRADUCCIONES)
        
        elif tipo == "clasificacion":
            drop_c = ['Notes', 'Goalkeeper', 'Top Team Scorer', 'Attendance', 'Pts/MP', 'Pts/PJ']
            df = df.drop(columns=[c for c in drop_c if c in df.columns])
            df = df.rename(columns=TRADUCCIONES)
            cols = list(df.columns)
            if 'EQUIPO' in cols and 'PTS' in cols:
                cols.remove('PTS')
                idx = cols.index('EQUIPO')
                cols.insert(idx + 1, 'PTS')
                df = df[cols]
                
        elif tipo == "fixture":
            drop_f = ['Day', 'Score', 'Referee', 'Match Report', 'Notes', 'Attendance', 'Wk']
            df = df.drop(columns=[c for c in drop_f if c in df.columns])
            df = df.rename(columns=TRADUCCIONES)
        
        # RESET DE ÍNDICE CRUCIAL PARA EVITAR KEYERROR EN STYLER
        return df.dropna(how='all').reset_index(drop=True)
    except: return None

# ────────────────────────────────────────────────
# LÓGICA DE CUOTAS (IGUAL QUE TU ORIGINAL)
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
    def extraer_nombre_puro(html_str):
        if '<span>' in str(html_str):
            res = re.search(r'<span>(.*?)</span>', html_str)
            return res.group(1) if res else html_str
        return html_str

    if df_clas is not None:
        puntos_dict = {extraer_nombre_puro(eq): pts for eq, pts in zip(df_clas.EQUIPO, df_clas.PTS)}
    else:
        puntos_dict = {}
    
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
    .table-container { width: 100%; overflow-x: auto; border: 1px solid #374151; border-radius: 8px; margin-bottom: 50px; }
    table { width: 100%; border-collapse: collapse; }
    th { position: sticky; top: 0; z-index: 100; background-color: #1f2937 !important; color: white !important; padding: 12px; border: 1px solid #374151; }
    td { padding: 12px; border: 1px solid #374151; text-align: left !important; }
    td:not(:nth-child(2)) { text-align: center !important; }
    .forma-container { display: flex; justify-content: center; gap: 4px; }
    .forma-box { width: 22px; height: 22px; line-height: 22px; text-align: center; border-radius: 4px; font-weight: bold; font-size: 11px; color: white; }
    .win { background-color: #137031; } .loss { background-color: #821f1f; } .draw { background-color: #82711f; }
    div.stButton > button { background-color: #ff1800 !important; color: white !important; font-weight: bold !important; border-radius: 8px; height: 45px; width: 100%; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div style="text-align:center; margin-bottom:20px;"><img src="https://i.postimg.cc/C516P7F5/33.png" width="300"></div>', unsafe_allow_html=True)

# ────────────────────────────────────────────────
# NAVEGACIÓN
# ────────────────────────────────────────────────
if "liga_sel" not in st.session_state: st.session_state.liga_sel = None
if "vista_activa" not in st.session_state: st.session_state.vista_activa = None
if "menu_op" not in st.session_state: st.session_state.menu_op = False

if st.button("COMPETENCIAS"):
    st.session_state.menu_op = not st.session_state.menu_op

if st.session_state.menu_op:
    sel = st.selectbox("Ligas", ["-- Selecciona --"] + LIGAS_LISTA, label_visibility="collapsed")
    if sel != "-- Selecciona --":
        st.session_state.liga_sel = sel
        st.session_state.menu_op = False
        st.session_state.vista_activa = None
        st.rerun()

if st.session_state.liga_sel:
    liga = st.session_state.liga_sel
    st.markdown(f'<div style="display: flex; align-items: center; gap: 15px; margin: 20px 0;"><img src="{BANDERAS.get(liga, "")}" style="width: 45px; border-radius: 4px;"><h1 style="color: white !important; font-size: 2rem; font-weight: bold; margin: 0;">{liga}</h1></div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("Clasificación"): st.session_state.vista_activa = "clas"
    if col2.button("Stats Generales"): st.session_state.vista_activa = "stats"
    if col3.button("Ver Fixture"): st.session_state.vista_activa = "fix"
    if col4.button("Picks & Cuotas"): st.session_state.vista_activa = "odds"

    st.divider()

    view = st.session_state.vista_activa
    if view:
        sufijo = MAPEO_ARCHIVOS.get(liga)
        df_clas_base = cargar_excel(f"CLASIFICACION_LIGA_{sufijo}.xlsx", "clasificacion")
        df_stats_base = cargar_excel(f"RESUMEN_STATS_{sufijo}.xlsx", "stats")

        if view == "odds":
            # Lógica de Cuotas simplificada para evitar errores de renderizado
            st.subheader("⚔️ Comparador H2H")
            if df_clas_base is not None:
                equipos_html = sorted(df_clas_base['EQUIPO'].unique())
                equipos_nombres = [re.search(r'<span>(.*?)</span>', e).group(1) for e in equipos_html if '<span>' in str(e)]
                
                col_h1, col_h2 = st.columns(2)
                eq_l_nom = col_h1.selectbox("Local", equipos_nombres, index=0)
                eq_v_nom = col_h2.selectbox("Visitante", equipos_nombres, index=1)
                
                d_l = df_clas_base[df_clas_base['EQUIPO'].str.contains(eq_l_nom)].iloc[0]
                d_v = df_clas_base[df_clas_base['EQUIPO'].str.contains(eq_v_nom)].iloc[0]
                
                st.markdown(f'<div style="background: linear-gradient(135deg, #1f2937 0%, #111827 100%); border: 1px solid #374151; border-radius: 12px; padding: 20px; margin-bottom: 25px;">Puntos: {d_l["PTS"]} vs {d_v["PTS"]}</div>', unsafe_allow_html=True)

            with st.spinner('Cargando mercado...'):
                raw = obtener_cuotas_api(liga)
                df_odds = procesar_cuotas(raw, df_clas_base)
                if df_odds is not None and not df_odds.empty:
                    st.dataframe(df_odds)

        else:
            configs = {"clas": (f"CLASIFICACION_LIGA_{sufijo}.xlsx", "clasificacion"), 
                       "stats": (f"RESUMEN_STATS_{sufijo}.xlsx", "stats"), 
                       "fix": (f"CARTELERA_PROXIMOS_{sufijo}.xlsx", "fixture")}
            archivo, tipo = configs[view]
            df = cargar_excel(archivo, tipo=tipo)
            
            if df is not None and not df.empty:
                if 'ÚLTIMOS 5' in df.columns: 
                    df['ÚLTIMOS 5'] = df['ÚLTIMOS 5'].apply(formatear_last_5)
                if 'xG_val' in df.columns: 
                    df = df.drop(columns=['xG_val'])
                
                # RENDERIZADO SEGURO
                try:
                    # Buscamos PTS de forma dinámica
                    col_pts = next((c for c in df.columns if 'PTS' in str(c).upper()), None)
                    
                    styler = df.style.hide(axis="index")
                    if col_pts:
                        styler = styler.set_properties(subset=[col_pts], **{'background-color': '#262730', 'font-weight': 'bold'})
                    
                    st.markdown(f'<div class="table-container">{styler.to_html(escape=False)}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error visualizando tabla: {e}")
                    st.dataframe(df) # Fallback si el styler falla

st.write("---")
st.caption("InsideBet Official | Sistema de análisis futbolístico")
