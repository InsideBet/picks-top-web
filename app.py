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
        bg = "#137031" if l == 'W' else "#821f1f" if l == 'L' else "#82711f"
        html_str += f'<span style="background-color: {bg}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; min-width: 18px; text-align: center;">{trad.get(l, l)}</span>'
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
            # No formateamos xG ni Poss aquí para poder usarlos en el H2H con números reales
            df = df.rename(columns=TRADUCCIONES)
            cols_ok = ['EQUIPO', 'PJ', 'POSESIÓN', 'GOLES', 'AST', 'AMARILLAS', 'ROJAS', 'xG', 'xG_val']
            df = df[[c for c in cols_ok if c in df.columns]]
        
        elif tipo == "clasificacion":
            if 'Squad' in df.columns:
                df['Squad'] = df['Squad'].apply(limpiar_nombre_equipo)
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
            df = df.rename(columns=TRADUCCIONES)
            if 'LOCAL' in df.columns:
                df['LOCAL'] = df['LOCAL'].apply(limpiar_nombre_equipo)
            if 'VISITANTE' in df.columns:
                df['VISITANTE'] = df['VISITANTE'].apply(limpiar_nombre_equipo)
            df = df[df.get('LOCAL', '') != ""]
        
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
    
    /* LOGO CENTRADO */
    .logo-center-wrapper {
        display: flex; justify-content: center; align-items: center;
        width: 100%; padding: 20px 0; margin-top: -30px;
    }
    .logo-center-wrapper img { width: 100%; max-width: 500px; height: auto; }

    /* BOTÓN COMPETENCIAS CIAN */
    div.stButton > button:first-child {
        background-color: #1ed7de !important;
        color: #000 !important;
        border: none !important;
        font-weight: bold !important;
        width: 200px !important;
        height: 45px !important;
        border-radius: 8px !important;
    }

    /* BOTONES NAVEGACIÓN */
    [data-testid="stHorizontalBlock"] button {
        background-color: transparent !important;
        color: #1ed7de !important;
        border: 1px solid #1ed7de !important;
    }

    /* TABLAS Y COMPARADOR */
    .table-container { 
        width: 100%; border: 1px solid #1ed7de44; 
        border-radius: 8px; background-color: #161b22; overflow: hidden;
    }
    .h2h-card {
        background: #1f2937; padding: 20px; border-radius: 12px;
        border-left: 5px solid #1ed7de; margin-bottom: 20px;
    }
    .h2h-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #374151; }
    .h2h-label { color: #9ca3af; font-size: 13px; text-transform: uppercase; }
    .h2h-val { font-weight: bold; color: white; }
    
    .bar-fill { background-color: #1ed7de; height: 100%; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# ESTRUCTURA
# ────────────────────────────────────────────────

st.markdown('<div class="logo-center-wrapper"><img src="https://i.postimg.cc/SKPzCcyV/33.png"></div>', unsafe_allow_html=True)

if "liga_sel" not in st.session_state: st.session_state.liga_sel = None
if "vista_activa" not in st.session_state: st.session_state.vista_activa = "clas"
if "menu_op" not in st.session_state: st.session_state.menu_op = False

if st.button("COMPETENCIAS"):
    st.session_state.menu_op = not st.session_state.menu_op

if st.session_state.menu_op:
    sel = st.selectbox("Ligas", ["---"] + LIGAS_LISTA, label_visibility="collapsed")
    if sel != "---":
        st.session_state.liga_sel = sel
        st.session_state.menu_op = False
        st.rerun()

if st.session_state.liga_sel:
    liga = st.session_state.liga_sel
    st.markdown(f'<h1 style="color:white; font-size:24px;"><img src="{BANDERAS.get(liga)}" width="35"> {liga}</h1>', unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("Clasificación", key="v1"): st.session_state.vista_activa = "clas"
    if c2.button("Stats Generales", key="v2"): st.session_state.vista_activa = "stats"
    if c3.button("Ver Fixture", key="v3"): st.session_state.vista_activa = "fix"
    if c4.button("Picks & Cuotas", key="v4"): st.session_state.vista_activa = "odds"

    st.divider()
    sufijo = MAPEO_ARCHIVOS.get(liga)
    df_clas = cargar_excel(f"CLASIFICACION_LIGA_{sufijo}.xlsx", "clasificacion")
    df_stats = cargar_excel(f"RESUMEN_STATS_{sufijo}.xlsx", "stats")

    if st.session_state.vista_activa == "odds":
        st.subheader("⚔️ Análisis H2H Pro")
        if df_clas is not None and df_stats is not None:
            col_sel1, col_sel2 = st.columns(2)
            eq1 = col_sel1.selectbox("Local", sorted(df_clas['EQUIPO'].unique()), index=0)
            eq2 = col_sel2.selectbox("Visitante", sorted(df_clas['EQUIPO'].unique()), index=1)
            
            # EXTRACCIÓN DE DATA COMPLETA PARA H2H
            try:
                s1 = df_stats[df_stats['EQUIPO'] == eq1].iloc[0]
                s2 = df_stats[df_stats['EQUIPO'] == eq2].iloc[0]
                c1_data = df_clas[df_clas['EQUIPO'] == eq1].iloc[0]
                c2_data = df_clas[df_clas['EQUIPO'] == eq2].iloc[0]

                st.markdown(f"""
                <div class="h2h-card">
                    <div style="display:grid; grid-template-columns: 1fr 100px 1fr; text-align:center; font-size:18px; font-weight:bold; margin-bottom:15px;">
                        <div style="color:#1ed7de;">{eq1}</div><div>VS</div><div style="color:#1ed7de;">{eq2}</div>
                    </div>
                    <div class="h2h-row"><span class="h2h-val">{c1_data['PTS']}</span><span class="h2h-label">Puntos Totales</span><span class="h2h-val">{c2_data['PTS']}</span></div>
                    <div class="h2h-row"><span class="h2h-val">{s1['GOLES']/s1['PJ']:.2f}</span><span class="h2h-label">Goles por Partido</span><span class="h2h-val">{s2['GOLES']/s2['PJ']:.2f}</span></div>
                    <div class="h2h-row"><span class="h2h-val">{s1['xG_val']:.2f}</span><span class="h2h-label">xG (Calidad Ataque)</span><span class="h2h-val">{s2['xG_val']:.2f}</span></div>
                    <div class="h2h-row"><span class="h2h-val">{s1['POSESIÓN']}</span><span class="h2h-label">Posesión Media</span><span class="h2h-val">{s2['POSESIÓN']}</span></div>
                    <div class="h2h-row"><span class="h2h-val">{s1['AMARILLAS']}</span><span class="h2h-label">Tarjetas Amarillas</span><span class="h2h-val">{s2['AMARILLAS']}</span></div>
                </div>
                """, unsafe_allow_html=True)
            except: st.warning("Datos de comparación no disponibles para estos equipos.")

        with st.spinner("Obteniendo cuotas..."):
            raw = obtener_cuotas_api(liga)
            df_o = procesar_cuotas(raw, df_clas)
            if df_o is not None and not df_o.empty:
                def aplicar_estilo_odds(row):
                    m = min(row['1'], row['X'], row['2'])
                    row['1'] = badge_cuota(row['1'], row['1']==m, row['VAL_H'])
                    row['X'] = badge_cuota(row['X'], row['X']==m)
                    row['2'] = badge_cuota(row['2'], row['2']==m)
                    return row
                res_odds = df_o.apply(aplicar_estilo_odds, axis=1)
                st.markdown(f'<div class="table-container">{res_odds[["FECHA","LOCAL","VISITANTE","1","X","2"]].style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

    else:
        # Vistas de Tablas Normales
        tipo_map = {"clas": "clasificacion", "stats": "stats", "fix": "fixture"}
        file_map = {"clas": f"CLASIFICACION_LIGA_{sufijo}.xlsx", "stats": f"RESUMEN_STATS_{sufijo}.xlsx", "fix": f"CARTELERA_PROXIMOS_{sufijo}.xlsx"}
        
        df = cargar_excel(file_map[st.session_state.vista_activa], tipo_map[st.session_state.vista_activa])
        if df is not None:
            # Post-procesado para visualización
            if 'ÚLTIMOS 5' in df.columns: df['ÚLTIMOS 5'] = df['ÚLTIMOS 5'].apply(formatear_last_5)
            if 'POSESIÓN' in df.columns: df['POSESIÓN'] = df['POSESIÓN'].apply(html_barra_posesion)
            if 'xG' in df.columns: df['xG'] = df['xG'].apply(formatear_xg_badge)
            if 'xG_val' in df.columns: df = df.drop(columns=['xG_val'])
            
            styler = df.style.hide(axis="index")
            if 'PTS' in df.columns:
                styler = styler.set_properties(subset=['PTS'], **{'background-color': '#1ed7de22', 'color': '#1ed7de', 'font-weight': 'bold'})
            st.markdown(f'<div class="table-container">{styler.to_html(escape=False)}</div>', unsafe_allow_html=True)

st.write("---")
st.caption("InsideBet Official | scrapeo")
