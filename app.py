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
        # Mantenemos carga para archivos originales (.xlsx) y el de jugadores (.csv)
        if nombre_archivo.endswith('.xlsx'):
            df = pd.read_excel(url)
        else:
            df = pd.read_csv(url)
        return df
    except:
        return None

# Nueva función para procesar los datos de scrapeo de jugadores
@st.cache_data(ttl=3600)
def cargar_datos_jugadores():
    url = f"{BASE_URL}/jugadoreswhoscored.csv"
    try:
        df = pd.read_csv(url)
        # Limpieza: Eliminamos los números (edad) pegados al nombre
        df['Jugador'] = df['Jugador'].str.replace(r'\d+$', '', regex=True)
        return df
    except:
        return None

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
        <div class=\"leyenda-container\">
            <div class=\"leyenda-item\"><span style=\"color:#22c55e; font-weight:bold;\">✅ Pick:</span><span>Resultado sugerido.</span></div>
            <div class=\"leyenda-item\"><span style=\"color:#facc15; font-weight:bold;\">📊 Prob:</span><span>Probabilidad más probable.</span></div>
            <div class=\"leyenda-item\"><span style=\"color:#3b82f6; font-weight:bold;\">💎 Value:</span><span>Apuesta con valor detectado.</span></div>
            <div class=\"leyenda-item\"><span style=\"color:#1ed7de; font-weight:bold;\">🔥 Over:</span><span>+2.5 Goles.</span></div>
            <div class=\"leyenda-item\"><span style=\"color:#9ca3af; font-weight:bold;\">🛡️ Under:</span><span>-2.5 Goles.</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(df_picks.style.hide(axis="index"), use_container_width=True)
    else:
        st.warning("No hay picks disponibles.")

else:
    # SECCIÓN STATS EQUIPOS
    configs = {"clas": (f"CLASIFICACION_LIGA_{sufijo}.xlsx", "clasificacion"), "stats": (f"RESUMEN_STATS_{sufijo}.xlsx", "stats"), "fix": (f"CARTELERA_PROXIMOS_{sufijo}.xlsx", "fixture")}
    archivo, tipo = configs[view]
    df = cargar_excel(archivo, tipo=tipo)
    if df is not None:
        if 'ÚLTIMOS 5' in df.columns: df['ÚLTIMOS 5'] = df['ÚLTIMOS 5'].apply(formatear_last_5)
        cols_to_drop = ['xG_val', 'Poss_num']
        df_view = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
        
        # --- FILTRO MEJORADO CON LISTA Y ESCRITURA ---
        equipos_lista = sorted(df['EQUIPO'].unique().tolist()) if 'EQUIPO' in df.columns else []
        col_busqueda, col_lista = st.columns([1, 1])
        with col_busqueda:
            busqueda = st.text_input("🔍 Escribir equipo...", "").strip().lower()
        with col_lista:
            seleccion_lista = st.selectbox("📋 O selecciona de la lista:", [""] + equipos_lista)
        
        # Priorizamos la selección de lista si existe, sino la búsqueda manual
        equipo_a_filtrar = seleccion_lista if seleccion_lista else busqueda
        
        if equipo_a_filtrar and 'EQUIPO' in df_view.columns: 
            df_view = df_view[df_view['EQUIPO'].str.lower().str.contains(equipo_a_filtrar.lower())]
        
        # Mantenemos intacto tu renderizado HTML
        styler = df_view.style.hide(axis="index")
        if 'PTS' in df_view.columns:
            styler = styler.background_gradient(subset=['PTS'], cmap='Greens')
        st.write(styler.to_html(escape=False), unsafe_allow_html=True)

        # --- INTEGRACIÓN DE JUGADORES (SCRAPEO) ---
        if equipo_a_filtrar:
            st.markdown(f"### 📋 Plantilla y Estadísticas de Jugadores")
            df_jug = cargar_datos_jugadores()
            if df_jug is not None:
                # Filtrar por equipo (coincidencia parcial) y liga (coincidencia exacta)
                filtro_final = df_jug[
                    (df_jug['Equipo'].str.lower().str.contains(equipo_a_filtrar.lower())) & 
                    (df_jug['Liga'] == liga_sel)
                ]
                
                if not filtro_final.empty:
                    # Aplicamos diccionario para que el apostador entienda (traducimos según tu lógica)
                    diccionario_vista = {
                        'Jugador': 'Jugador', 'Mins': '⏱️ Minutos', 'Rating': '⭐ Rating',
                        'Amarillas': '🟨', 'Rojas': '🟥', 'Entradas_Std': '🛡️ Entradas',
                        'Regates_p90': '⚡ Regates(p90)', 'Goles': '⚽ Goles', 'Asistencias': '🅰️ Asist',
                        'Pases Clave': '🔑 P.Clave', 'Tiros_Arco_p90': '🎯 Tiros(p90)',
                        'Faltas recibidas': '🤕 F.Rec'
                    }
                    # Seleccionamos y renombramos solo las columnas que existen en el excel
                    cols_presentes = [c for c in diccionario_vista.keys() if c in filtro_final.columns]
                    df_jug_ver = filtro_final[cols_presentes].rename(columns=diccionario_vista)
                    
                    # Mostramos los jugadores. No tocamos estilos para mantener coherencia.
                    st.dataframe(df_jug_ver.style.hide(axis="index"), use_container_width=True)
                else:
                    st.info(f"No se encontraron datos de jugadores para {equipo_a_filtrar}.")

st.markdown("---")
st.caption("© 2026 InsideBet - Datos actualizados vía scrapeo.")
