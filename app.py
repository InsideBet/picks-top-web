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
    "Bundesliga": "Bundesliga", "Ligue_1": "Ligue_1", "Primeira Liga": "Primeira_Liga",
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
    html_str = '<div class="forma-container">'
    for l in letras:
        clase = "win" if l == 'W' else "loss" if l == 'L' else "draw" if l == 'D' else ""
        html_str += f'<span class="forma-box {clase}">{trad.get(l, l)}</span>'
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
# LÓGICA DE CUOTAS Y MEJORAS SMART
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

def badge_cuota(val, es_minimo=False, tiene_valor=False, termometro=0):
    color_bg = "#b59410" if tiene_valor else ("#137031" if es_minimo else "#2d3139")
    color_text = "white" if tiene_valor else ("#00ff88" if es_minimo else "#ced4da")
    label = " ⭐" if tiene_valor else ""
    # Mini barra de termómetro de valor
    term_html = ""
    if tiene_valor:
        ancho = min(termometro * 2, 100) # Escalado
        term_html = f'<div style="width:100%; background:#2d3139; height:3px; margin-top:2px; border-radius:2px;"><div style="width:{ancho}%; background:#ffd700; height:100%;"></div></div>'
    
    return f'''
    <div style="display: flex; flex-direction: column; align-items: center;">
        <span style="background-color: {color_bg}; color: {color_text}; padding: 5px 12px; border-radius: 6px; font-weight: bold; font-size: 13px; min-width: 60px; text-align: center; border: 1px solid #4b5563;">
            {val:.2f}{label}
        </span>
        {term_html}
    </div>
    '''

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
        
        val_h, desfase = False, 0
        if home in puntos_dict and away in puntos_dict:
            pts_h, pts_a = puntos_dict[home], puntos_dict[away]
            prob_est = (pts_h + 5) / (pts_h + pts_a + 10)
            cuota_esperada = 1 / prob_est
            if h > (cuota_esperada * 1.15): 
                val_h = True
                desfase = int(((h / cuota_esperada) - 1) * 100)
            
        rows.append({"FECHA": commence, "LOCAL": home, "VISITANTE": away, "1": h, "X": d, "2": a, "VAL_H": val_h, "TERM": desfase})
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
    td { padding: 12px; border: 1px solid #374151; text-align: center !important; }
    .fatiga-tag { color: #ff4b4b; font-size: 0.75rem; font-weight: bold; display: block; margin-top: 2px; }
    .escenario-tag { font-size: 0.8rem; font-weight: 500; padding: 2px 6px; border-radius: 4px; background: #2d3139; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div style="text-align:center; margin-bottom:20px;"><img src="https://i.postimg.cc/C516P7F5/33.png" width="300"></div>', unsafe_allow_html=True)

# ────────────────────────────────────────────────
# LÓGICA DE NAVEGACIÓN
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
    st.markdown(f'<div class="header-container"><img src="{BANDERAS.get(liga, "")}" class="flag-img"><h1 class="header-title">{liga}</h1></div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("Clasificación"): st.session_state.vista_activa = "clas" if st.session_state.vista_activa != "clas" else None
    if col2.button("Stats Generales"): st.session_state.vista_activa = "stats" if st.session_state.vista_activa != "stats" else None
    if col3.button("Ver Fixture"): st.session_state.vista_activa = "fix" if st.session_state.vista_activa != "fix" else None
    if col4.button("Picks & Cuotas"): st.session_state.vista_activa = "odds" if st.session_state.vista_activa != "odds" else None

    st.divider()

    view = st.session_state.vista_activa
    if view:
        sufijo = MAPEO_ARCHIVOS.get(liga)
        df_clas_base = cargar_excel(f"CLASIFICACION_LIGA_{sufijo}.xlsx", "clasificacion")
        df_stats_base = cargar_excel(f"RESUMEN_STATS_{sufijo}.xlsx", "stats")
        df_champions = cargar_excel(f"CLASIFICACION_LIGA_Champions_League.xlsx", "clasificacion") if liga != "Champions League" else None

        if view == "odds":
            with st.spinner('Calculando Modelos Smart...'):
                raw = obtener_cuotas_api(liga)
                df_odds = procesar_cuotas(raw, df_clas_base)
                if df_odds is not None and not df_odds.empty:
                    
                    def aplicar_mejoras(r):
                        # 1. Escenario xG
                        escenario = "---"
                        try:
                            xg_l = float(df_stats_base[df_stats_base['EQUIPO'] == r['LOCAL']]['xG_val'].values[0])
                            xg_v = float(df_stats_base[df_stats_base['EQUIPO'] == r['VISITANTE']]['xG_val'].values[0])
                            if xg_l > 1.7 and xg_v < 1.0: escenario = "🎯 Ataque vs Defensa"
                            elif xg_l > 1.6 and xg_v > 1.6: escenario = "🥊 Intercambio"
                            elif xg_l < 1.1 and xg_v < 1.1: escenario = "🛡️ Partido Cerrado"
                            else: escenario = "📊 Proyección Media"
                        except: pass
                        r['ESCENARIO'] = f'<span class="escenario-tag">{escenario}</span>'

                        # 2. Fatiga Champions
                        aviso_l, aviso_v = "", ""
                        if df_champions is not None:
                            if r['LOCAL'] in df_champions['EQUIPO'].values: aviso_l = '<span class="fatiga-tag">⚠️ Fatiga UCL</span>'
                            if r['VISITANTE'] in df_champions['EQUIPO'].values: aviso_v = '<span class="fatiga-tag">⚠️ Fatiga UCL</span>'
                        
                        r['LOCAL'] = f"{r['LOCAL']}{aviso_l}"
                        r['VISITANTE'] = f"{r['VISITANTE']}{aviso_v}"

                        # 3. Estilo Cuotas + Termómetro
                        m = min(r['1'], r['X'], r['2'])
                        r['1'] = badge_cuota(r['1'], r['1']==m, r['VAL_H'], r['TERM'])
                        r['X'] = badge_cuota(r['X'], r['X']==m)
                        r['2'] = badge_cuota(r['2'], r['2']==m)
                        return r
                    
                    df_final = df_odds.apply(aplicar_mejoras, axis=1)
                    cols_mostrar = ['FECHA','LOCAL','VISITANTE','1','X','2','ESCENARIO']
                    html = df_final[cols_mostrar].style.hide(axis="index").to_html(escape=False)
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
                if 'PTS' in df.columns: styler = styler.set_properties(subset=['PTS'], **{'background-color': '#262730', 'font-weight': 'bold'})
                st.markdown(f'<div class="table-container">{styler.to_html(escape=False)}</div>', unsafe_allow_html=True)

st.write("---")
st.caption("InsideBet Official | Sistema de análisis futbolístico")
