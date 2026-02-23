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
        df = pd.read_excel(url) if nombre_archivo.endswith('.xlsx') else pd.read_csv(url)
        return df
    except:
        return None

@st.cache_data(ttl=3600)
def cargar_jugadores():
    # El archivo de scrapeo que subiste
    url_jugadores = f"{BASE_URL}/jugadoreswhoscored.csv"
    try:
        df = pd.read_csv(url_jugadores)
        # Limpieza: Solo el nombre (quitamos los números de edad al final)
        df['Jugador'] = df['Jugador'].str.replace(r'\d+$', '', regex=True)
        return df
    except:
        return None

def formatear_columnas_jugadores(df):
    # Diccionario para que el apostador entienda el scrapeo
    diccionario_stats = {
        'Jugador': 'Jugador', 
        'Mins': '⏱️ Minutos', 
        'Rating': '⭐ Rating',
        'Amarillas': '🟨', 
        'Rojas': '🟥', 
        'Entradas_Std': '🛡️ Entradas',
        'Regates_p90': '⚡ Regates(p90)', 
        'Goles': '⚽ Goles', 
        'Asistencias': '🅰️ Asist',
        'Pases': 'Pas', 
        'Pases Clave': '🔑 P.Clave', 
        'Tiros_Arco_p90': '🎯 Tiros(p90)',
        'Tiros_Fuera_p90': '🥅 Fuera(p90)', 
        'Faltas': 'Faltas', 
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
            <div class="leyenda-item"><span style="color:#facc15; font-weight:bold;">📊 Prob:</span><span>Probabilidad calculada.</span></div>
            <div class="leyenda-item"><span style="color:#3b82f6; font-weight:bold;">💎 Value:</span><span>Apuesta con valor.</span></div>
            <div class="leyenda-item"><span style="color:#1ed7de; font-weight:bold;">🔥 Over:</span><span>+2.5 Goles.</span></div>
            <div class="leyenda-item"><span style="color:#9ca3af; font-weight:bold;">🛡️ Under:</span><span>-2.5 Goles.</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(df_picks.style.hide(axis="index"), use_container_width=True)
    else:
        st.warning("No hay picks disponibles para esta liga en este momento.")

else:
    st.subheader(f"📊 Estadísticas de Equipos: {liga_sel}")
    tab_c, tab_s, tab_f = st.tabs(["🏆 Clasificación", "📈 Stats Avanzadas", "🗓️ Próximos Partidos"])

    vistas_map = {"🏆 Clasificación": "clas", "📈 Stats Avanzadas": "stats", "🗓️ Próximos Partidos": "fix"}
    view_sub = vistas_map[st.session_state.get('current_tab', "🏆 Clasificación")]
    
    # Lógica unificada para las 3 pestañas de Stats Equipos
    for tab, v_key in zip([tab_c, tab_s, tab_f], ["clas", "stats", "fix"]):
        with tab:
            configs = {
                "clas": (f"CLASIFICACION_LIGA_{sufijo}.xlsx", "clasificacion"), 
                "stats": (f"RESUMEN_STATS_{sufijo}.xlsx", "stats"), 
                "fix": (f"CARTELERA_PROXIMOS_{sufijo}.xlsx", "fixture")
            }
            archivo, tipo = configs[v_key]
            df = cargar_excel(archivo, tipo=tipo)

            if df is not None:
                if 'ÚLTIMOS 5' in df.columns: 
                    df['ÚLTIMOS 5'] = df['ÚLTIMOS 5'].apply(formatear_last_5)
                
                # --- SISTEMA DE FILTRADO MEJORADO ---
                equipos_disponibles = sorted(df['EQUIPO'].unique().tolist()) if 'EQUIPO' in df.columns else []
                col_f1, col_f2 = st.columns([1, 1])
                with col_f1:
                    busqueda = st.text_input(f"🔍 Escribir nombre del equipo ({v_key})...", "").strip().lower()
                with col_f2:
                    seleccion = st.selectbox(f"📋 Seleccionar de la lista ({v_key}):", [""] + equipos_disponibles)
                
                equipo_final = seleccion if seleccion else busqueda
                
                df_view = df.copy()
                if equipo_final and 'EQUIPO' in df_view.columns:
                    df_view = df_view[df_view['EQUIPO'].str.lower().str.contains(equipo_final.lower())]

                # Quitar columnas innecesarias para el usuario
                cols_to_drop = ['xG_val', 'Poss_num']
                df_view = df_view.drop(columns=[c for c in cols_to_drop if c in df_view.columns])

                st.write(df_view.to_html(escape=False, index=False), unsafe_allow_html=True)

                # --- INTEGRACIÓN DEL SCRAPEO DE JUGADORES ---
                if equipo_final:
                    st.markdown(f"### 🏟️ Plantilla y Estadísticas de Jugadores: {equipo_final}")
                    df_jugadores_raw = cargar_jugadores()
                    
                    if df_jugadores_raw is not None:
                        # El excel tiene columnas 'Equipo' y 'Liga'
                        # Filtramos por equipo (parcial) y por liga exacta
                        filtro_jug = df_jugadores_raw[
                            (df_jugadores_raw['Equipo'].str.lower().str.contains(equipo_final.lower())) & 
                            (df_jugadores_raw['Liga'] == liga_sel)
                        ]
                        
                        if not filtro_jug.empty:
                            # Quitamos columnas de control y aplicamos el diccionario de traducción
                            df_jug_display = filtro_jug.drop(columns=['Equipo', 'Liga'])
                            df_jug_display = formatear_columnas_jugadores(df_jug_display)
                            
                            # Estilo: Resaltamos el Rating para ver a los mejores
                            st.dataframe(
                                df_jug_display.style.background_gradient(subset=['⭐ Rating'], cmap='Greens').hide(axis="index"), 
                                use_container_width=True
                            )
                        else:
                            st.info(f"No hay datos de jugadores disponibles para {equipo_final} en {liga_sel}.")
                    else:
                        st.error("No se pudo cargar el archivo de jugadores desde el repositorio.")

            else:
                st.info(f"No hay datos disponibles para la sección {v_key} de esta liga.")

st.markdown("---")
st.caption(f"© 2026 InsideBet - Datos de **scrapeo** actualizados.")
