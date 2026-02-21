import streamlit as st
import pandas as pd
import numpy as np
import re
import requests

# ────────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ────────────────────────────────────────────────
st.set_page_config(page_title="InsideBet", layout="wide")

# Token de seguridad / Palabras clave del usuario
# scrapeo 

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

# ────────────────────────────────────────────────
# FUNCIONES AUXILIARES
# ────────────────────────────────────────────────

def limpiar_nombre_equipo(nombre):
    if pd.isna(nombre) or str(nombre).lower() == 'nan': return ""
    txt = str(nombre).strip()
    txt = re.sub(r'^[a-z]{2,3}\s+', '', txt, flags=re.IGNORECASE)
    txt = re.sub(r'\s+[a-z]{2,3}$', '', txt, flags=re.IGNORECASE)
    return txt.strip()

@st.cache_data(ttl=600)
def cargar_excel(ruta_archivo, tipo="general"):
    # Si es el archivo de jugadores, va a la subcarpeta
    if "SUPER_STATS" in ruta_archivo:
        url = f"{BASE_URL}/Estadisticas_Jugadores/{ruta_archivo}"
    else:
        url = f"{BASE_URL}/{ruta_archivo}"
        
    try:
        df = pd.read_excel(url)
        # Limpieza estándar de equipos
        if 'Squad' in df.columns:
            df['Squad'] = df['Squad'].apply(limpiar_nombre_equipo)
        return df
    except Exception as e:
        return None

def calcular_confianza_equipo(nombre_equipo, df_stats):
    """Calcula un score de 0 a 100 basado en xG y Goles."""
    try:
        if df_stats is None: return 50
        # Buscamos al equipo en el resumen de stats
        row = df_stats[df_stats['Squad'] == nombre_equipo].iloc[0]
        # Algoritmo simple: Goles y xG (suponiendo que xG es columna 16)
        xg = float(row.iloc[16]) if len(row) > 16 else 1.0
        goles = float(row['Gls']) if 'Gls' in row else 1.0
        score = int(min(((xg * 0.6) + (goles * 0.4)) * 10, 100))
        return max(score, 10)
    except:
        return 50

def html_barra_posesion(valor):
    try:
        num = float(str(valor).replace('%', ''))
        percent = min(max(int(num), 0), 100)
        return f'<div style="width:100%; background:#2d3139; border-radius:4px; height:15px;"><div style="width:{percent}%; background:#1ed7de; height:100%; border-radius:4px;"></div></div>'
    except: return valor

# ────────────────────────────────────────────────
# ESTILOS CSS
# ────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e5e7eb; }
    .main-logo-container { text-align: center; padding: 20px 0; }
    .main-logo-img { width: 50%; max-width: 400px; }
    .table-container { width: 100%; overflow-x: auto; border: 1px solid #1ed7de33; border-radius: 8px; background: #161b22; margin-top: 10px; }
    table { width: 100%; border-collapse: collapse; }
    th { background-color: #1f2937 !important; color: #1ed7de !important; padding: 12px; text-align: center !important; }
    td { padding: 10px; border-bottom: 1px solid #374151; text-align: center !important; font-size: 14px; }
    .badge-conf { background: #1ed7de22; color: #1ed7de; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 11px; }
    .cuota-box { background: #2d3139; border: 1px solid #4b5563; padding: 4px 10px; border-radius: 5px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# CUERPO DE LA APP
# ────────────────────────────────────────────────
st.markdown('<div class="main-logo-container"><img src="https://i.postimg.cc/SKPzCcyV/33.png" class="main-logo-img"></div>', unsafe_allow_html=True)

if "liga_sel" not in st.session_state: st.session_state.liga_sel = None
if "vista" not in st.session_state: st.session_state.vista = "Clasificación"

# Botón desplegable principal
if st.button("🏆 SELECCIONAR COMPETENCIA", use_container_width=True):
    st.session_state.show_menu = not st.session_state.get('show_menu', False)

if st.session_state.get('show_menu'):
    sel = st.selectbox("Ligas disponibles", ["-"] + LIGAS_LISTA, label_visibility="collapsed")
    if sel != "-":
        st.session_state.liga_sel = sel
        st.session_state.show_menu = False
        st.rerun()

if st.session_state.liga_sel:
    liga = st.session_state.liga_sel
    suf = MAPEO_ARCHIVOS[liga]
    
    # Header de Liga
    st.markdown(f'''
        <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
            <img src="{BANDERAS[liga]}" width="50">
            <h1 style="margin:0; color:white;">{liga}</h1>
        </div>
    ''', unsafe_allow_html=True)

    # Botonera de Navegación
    c1, c2, c3, c4, c5 = st.columns(5)
    vistas = ["Clasificación", "Stats Equipos", "Análisis Jugadores", "Fixture", "Picks & Cuotas"]
    btns = [c1, c2, c3, c4, c5]
    
    for i, v in enumerate(vistas):
        if btns[i].button(v, use_container_width=True):
            st.session_state.vista = v

    st.divider()

    # Carga de datos base
    df_clas = cargar_excel(f"CLASIFICACION_LIGA_{suf}.xlsx")
    df_resumen = cargar_excel(f"RESUMEN_STATS_{suf}.xlsx")

    # --- LÓGICA DE VISTAS ---
    
    if st.session_state.vista == "Clasificación" and df_clas is not None:
        st.markdown(f'<div class="table-container">{df_clas.to_html(index=False, escape=False)}</div>', unsafe_allow_html=True)

    elif st.session_state.vista == "Stats Equipos" and df_resumen is not None:
        # Aplicamos barra de posesión si existe la columna
        df_view = df_resumen.copy()
        if 'Poss' in df_view.columns:
            df_view['Poss'] = df_view['Poss'].apply(html_barra_posesion)
        st.markdown(f'<div class="table-container">{df_view.to_html(index=False, escape=False)}</div>', unsafe_allow_html=True)

    elif st.session_state.vista == "Análisis Jugadores":
        df_p = cargar_excel(f"SUPER_STATS_{suf}.xlsx")
        if df_p is not None:
            # Filtros Pro
            f1, f2, f3 = st.columns([2,1,1])
            with f1: 
                eq_list = ["Todos"] + sorted(df_p['Squad'].unique().tolist())
                eq_sel = st.selectbox("Filtrar por Equipo", eq_list)
            with f2:
                pos_sel = st.multiselect("Posición", df_p['Pos'].unique(), default=df_p['Pos'].unique())
            with f3:
                min_min = st.number_input("Minutos mínimos", value=90, step=45)

            # Aplicar Filtros
            mask = (df_p['Min'] >= min_min) & (df_p['Pos'].isin(pos_sel))
            if eq_sel != "Todos":
                mask = mask & (df_p['Squad'] == eq_sel)
            
            df_filtered = df_p[mask].copy()

            t1, t2 = st.tabs(["🎯 ATAQUE Y REMATES", "🛡️ DISCIPLINA"])
            with t1:
                cols_atk = ["Player", "Squad", "Pos", "Gls", "Ast", "Sh", "SoT"]
                st.markdown(f'<div class="table-container">{df_filtered[cols_atk].to_html(index=False)}</div>', unsafe_allow_html=True)
            with t2:
                cols_def = ["Player", "Squad", "Fls", "Fld", "CrdY", "CrdR"]
                st.markdown(f'<div class="table-container">{df_filtered[cols_def].to_html(index=False)}</div>', unsafe_allow_html=True)
        else:
            st.warning("⚠️ No se encontraron estadísticas detalladas de jugadores para esta liga.")

    elif st.session_state.vista == "Picks & Cuotas":
        # Aquí integramos la confianza al lado de los equipos
        st.info("Obteniendo cuotas en tiempo real...")
        # Simulación/Lógica de cuotas (para no saturar la API en el ejemplo)
        # Aquí iría tu llamada a requests.get(url_odds)
        st.write("Sección en mantenimiento: Conectando con API de Cuotas.")

st.write("---")
st.caption("InsideBet | Data System v2.0 | scrapeo")
