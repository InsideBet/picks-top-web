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

# ────────────────────────────────────────────────
# FUNCIONES DE CARGA Y PROCESAMIENTO
# ────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def cargar_excel(nombre_archivo, tipo="stats"):
    url = f"{BASE_URL}/{nombre_archivo}"
    try:
        # Intentar leer como excel, si falla (porque ahora es CSV), leer como CSV
        if nombre_archivo.endswith('.xlsx'):
            df = pd.read_excel(url)
        else:
            df = pd.read_csv(url)
        return df
    except:
        return None

@st.cache_data(ttl=3600)
def cargar_jugadores():
    # El archivo del scrapeo de hoy
    url_jugadores = f"{BASE_URL}/jugadoreswhoscored.csv"
    try:
        df = pd.read_csv(url_jugadores)
        # Limpieza: Eliminamos los números al final del nombre (edad)
        df['Jugador'] = df['Jugador'].str.replace(r'\d+$', '', regex=True)
        return df
    except:
        return None

def formatear_columnas_jugadores(df):
    # Diccionario para que el apostador entienda el scrapeo
    diccionario_stats = {
        'Jugador': 'Jugador', 
        'Mins': '⏱️ Min', 
        'Rating': '⭐ Rating',
        'Amarillas': '🟨', 
        'Rojas': '🟥', 
        'Entradas_Std': '🛡️ Entradas',
        'Regates_p90': '⚡ Reg(p90)', 
        'Goles': '⚽ Goles', 
        'Asistencias': '🅰️ Asist',
        'Pases': 'Pas', 
        'Pases Clave': '🔑 P.Clave', 
        'Tiros_Arco_p90': '🎯 Tiros(p90)',
        'Tiros_Fuera_p90': '🥅 Fuera(p90)', 
        'Faltas': 'Fal', 
        'Faltas recibidas': '🤕 F.Rec'
    }
    return df.rename(columns=diccionario_stats)

def formatear_last_5(val):
    if not val or pd.isna(val): return ""
    res = []
    for char in str(val).upper():
        if char == 'W': res.append('<span style="color:#22c55e; font-weight:bold;">W</span>')
        elif char == 'L': res.append('<span style="color:#ef4444; font-weight:bold;">L</span>')
        elif char == 'D': res.append('<span style="color:#9ca3af; font-weight:bold;">D</span>')
    return f'<div style="display:flex; gap:5px;">{" ".join(res)}</div>'

# ────────────────────────────────────────────────
# INTERFAZ STREAMLIT
# ────────────────────────────────────────────────

st.markdown("""
<style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stDataFrame { border: 1px solid #30363d; border-radius: 10px; }
    .leyenda-container { display: flex; flex-wrap: wrap; gap: 15px; background: #161b22; padding: 10px; border-radius: 8px; margin-bottom: 20px; }
    .leyenda-item { display: flex; align-items: center; gap: 5px; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ InsideBet - Stats & Picks")

col1, col2 = st.columns([1, 1])
with col1:
    liga_sel = st.selectbox("Selecciona una Liga", LIGAS_LISTA)
with col2:
    view = st.radio("Sección", ["Picks Pro", "Stats Equipos"], horizontal=True)

sufijo = MAPEO_ARCHIVOS.get(liga_sel, "Premier_League")

if view == "Picks Pro":
    st.subheader(f"🔥 Picks Sugeridos: {liga_sel}")
    archivo_picks = f"PREDICCIONES_{sufijo}.xlsx"
    df_picks = cargar_excel(archivo_picks, tipo="picks")

    if df_picks is not None:
        st.markdown("""
        <div class="leyenda-container">
            <div class="leyenda-item"><span style="color:#22c55e; font-weight:bold;">✅ Pick:</span><span>Resultado sugerido.</span></div>
            <div class="leyenda-item"><span style="color:#facc15; font-weight:bold;">📊 Prob:</span><span>Probabilidad más probable.</span></div>
            <div class="leyenda-item"><span style="color:#3b82f6; font-weight:bold;">💎 Value:</span><span>Apuesta con valor detectado.</span></div>
            <div class="leyenda-item"><span style="color:#1ed7de; font-weight:bold;">🔥 Over:</span><span>+2.5 Goles.</span></div>
            <div class="leyenda-item"><span style="color:#9ca3af; font-weight:bold;">🛡️ Under:</span><span>-2.5 Goles.</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(df_picks.style.hide(axis="index"), use_container_width=True)
    else:
        st.warning("No hay picks disponibles para esta liga en este momento.")

else:
    st.subheader(f"📊 Estadísticas de Equipos: {liga_sel}")
    
    # Mantenemos tus 3 pestañas originales
    tab_c, tab_s, tab_f = st.tabs(["🏆 Clasificación", "📈 Stats Avanzadas", "🗓️ Próximos Partidos"])
    
    # Diccionario para mapear pestañas a archivos
    vistas_config = {
        "clas": (f"CLASIFICACION_LIGA_{sufijo}.xlsx", "clasificacion", tab_c),
        "stats": (f"RESUMEN_STATS_{sufijo}.xlsx", "stats", tab_s),
        "fix": (f"CARTELERA_PROXIMOS_{sufijo}.xlsx", "fixture", tab_f)
    }

    for v_key, (archivo, tipo, tab_obj) in vistas_config.items():
        with tab_obj:
            df = cargar_excel(archivo, tipo=tipo)
            if df is not None:
                if 'ÚLTIMOS 5' in df.columns: 
                    df['ÚLTIMOS 5'] = df['ÚLTIMOS 5'].apply(formatear_last_5)
                
                cols_to_drop = ['xG_val', 'Poss_num']
                df_view = df.drop(columns=[c for c in cols_to_drop if c in df.columns])

                # --- FILTRO MEJORADO (INPUT + SELECTBOX) ---
                equipos_disponibles = sorted(df['EQUIPO'].unique().tolist()) if 'EQUIPO' in df.columns else []
                col_f1, col_f2 = st.columns([1, 1])
                with col_f1:
                    busqueda = st.text_input(f"🔍 Escribir nombre ({v_key})...", "", key=f"input_{v_key}").strip().lower()
                with col_f2:
                    seleccion = st.selectbox(f"📋 Elegir de la lista ({v_key}):", [""] + equipos_disponibles, key=f"select_{v_key}")
                
                equipo_final = seleccion if seleccion else busqueda
                
                if equipo_final and 'EQUIPO' in df_view.columns:
                    df_view = df_view[df_view['EQUIPO'].str.lower().str.contains(equipo_final.lower())]

                st.write(df_view.to_html(escape=False, index=False), unsafe_allow_html=True)

                # --- INTEGRACIÓN DE JUGADORES (DEL SCRAPEO) ---
                if equipo_final:
                    st.markdown(f"#### ⚽ Plantilla y Stats: {equipo_final}")
                    df_jugadores = cargar_jugadores()
                    
                    if df_jugadores is not None:
                        # Filtrar por el equipo seleccionado y la liga actual
                        f_jug = df_jugadores[
                            (df_jugadores['Equipo'].str.lower().str.contains(equipo_final.lower())) & 
                            (df_jugadores['Liga'] == liga_sel)
                        ]
                        
                        if not f_jug.empty:
                            # Aplicamos diccionario y quitamos columnas de sistema
                            df_jug_fmt = f_jug.drop(columns=['Equipo', 'Liga'])
                            df_jug_fmt = formatear_columnas_jugadores(df_jug_fmt)
                            
                            # Mostramos la tabla con el Rating resaltado
                            st.dataframe(
                                df_jug_fmt.style.background_gradient(subset=['⭐ Rating'], cmap='Greens').hide(axis="index"),
                                use_container_width=True
                            )
                        else:
                            st.info("Datos de jugadores no encontrados para este equipo.")
            else:
                st.info(f"No hay datos para {v_key} en esta liga.")

st.markdown("---")
st.caption(f"© 2026 InsideBet - Análisis basado en **scrapeo** de datos avanzado.")
