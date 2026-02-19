import streamlit as st
import pandas as pd
import numpy as np

# ────────────────────────────────────────────────
# CONFIGURACIÓN
# ────────────────────────────────────────────────
st.set_page_config(page_title="InsideBet", layout="wide")

USER = "InsideBet" 
REPO = "picks-top-web"
BASE_URL = f"https://raw.githubusercontent.com/{USER}/{REPO}/main/datos_fbref"

LIGAS = {
    "PL": "Premier League", "PD": "La Liga", "SA": "Serie A",
    "BL1": "Bundesliga", "FL1": "Ligue 1", "PPL": "Primeira Liga",
    "DED": "Eredivisie", "CL": "Champions League"
}

MAPEO_ARCHIVOS = {
    "Premier League": "Premier_League", "La Liga": "La_Liga", "Serie A": "Serie_A",
    "Bundesliga": "Bundesliga", "Ligue 1": "Ligue_1", "Primeira Liga": "Primeira_Liga",
    "Eredivisie": "Eredivisie", "Champions League": "Champions_League"
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
# ESTILO CSS
# ────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e5e7eb; }
    
    .table-scroll {
        width: 100%;
        max-height: 450px; 
        overflow-x: auto !important;
        overflow-y: auto !important;
        display: block;
        border: 1px solid #374151;
        border-radius: 8px;
        margin-bottom: 20px;
    }

    .table-scroll::-webkit-scrollbar { width: 8px; height: 8px; }
    .table-scroll::-webkit-scrollbar-thumb { background: #ff1800; border-radius: 10px; }
    .table-scroll::-webkit-scrollbar-track { background: #1f2937; }

    .table-scroll table { min-width: 900px; width: 100%; border-collapse: collapse; }

    .table-scroll th {
        position: sticky; top: 0; z-index: 10;
        background-color: #1f2937 !important;
        color: #e5e7eb; padding: 12px; border: 1px solid #374151;
        font-size: 13px; text-align: center !important;
    }

    td { padding: 10px; border: 1px solid #374151; font-size: 14px; text-align: center !important; white-space: nowrap !important; }
    tr:hover { background-color: #21262d; }

    /* Estilo para la barra de posesión */
    .bar-container {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        gap: 10px;
        width: 180px; /* Ancho fijo para la columna de posesión */
        margin: 0 auto;
    }
    .bar-bg {
        background-color: #2d3139;
        border-radius: 10px;
        flex-grow: 1;
        height: 8px;
        overflow: hidden;
        position: relative;
    }
    .bar-fill {
        background-color: #ff4b4b; /* Rojo similar a tu imagen */
        height: 100%;
        border-radius: 10px;
    }
    .bar-text {
        font-size: 13px;
        font-weight: bold;
        min-width: 35px;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# FUNCIONES DE PROCESAMIENTO
# ────────────────────────────────────────────────

def color_xg_celda(val, min_val, max_val):
    try:
        val = float(val)
        tercio = (max_val - min_val) / 3
        if val >= min_val + 2 * tercio: color = "#137031" # Verde
        elif val >= min_val + tercio: color = "#82711f" # Amarillo
        else: color = "#821f1f" # Rojo
        return f'background-color: {color}; color: white; font-weight: bold;'
    except: return ''

def html_barra_posesion(valor):
    try:
        # Limpiar el valor si viene como string con % o decimales
        num = float(str(valor).replace('%', ''))
        if num > 100: num = num / 100 # Por si viene en formato 0.57
        percent = int(round(num if num > 1 else num * 100))
        
        return f'''
        <div class="bar-container">
            <div class="bar-bg">
                <div class="bar-fill" style="width: {percent}%;"></div>
            </div>
            <div class="bar-text">{percent}%</div>
        </div>
        '''
    except:
        return valor

def formatear_last_5(valor):
    if pd.isna(valor): return ""
    trad = {'W': 'G', 'L': 'P', 'D': 'E'}
    letras = list(str(valor).upper().replace(" ", ""))[:5]
    html_str = '<div class="forma-container">'
    for l in letras:
        clase = "win" if l == 'W' else "loss" if l == 'L' else "draw" if l == 'D' else ""
        html_str += f'<span class="forma-box {clase}">{trad.get(l, l)}</span>'
    html_str += '</div>'
    return html_str

@st.cache_data(ttl=300)
def cargar_excel(ruta_archivo, tipo="general"):
    url = f"{BASE_URL}/{ruta_archivo}"
    try:
        df = pd.read_excel(url)
        df.columns = [str(c).strip() for c in df.columns]

        if tipo == "stats":
            # Búsqueda flexible de xG (a veces FBRef lo llama de varias formas)
            posibles_xg = ['xG', 'Expected Goals', 'xG_total', 'Expected']
            col_xg_real = next((c for c in posibles_xg if c in df.columns), None)
            
            columnas_interes = ['Squad', 'MP', 'Poss', 'Gls', 'Ast', 'CrdY', 'CrdR']
            if col_xg_real:
                columnas_interes.append(col_xg_real)
            
            df = df[[c for c in columnas_interes if c in df.columns]]
            
            # Renombrar la columna xG encontrada al nombre estándar para el traductor
            if col_xg_real:
                df = df.rename(columns={col_xg_real: 'xG'})

            # Aplicar la barra visual a la Posesión
            if 'Poss' in df.columns:
                df['Poss'] = df['Poss'].apply(html_barra_posesion)

        # Tratar otras secciones
        elif tipo == "clasificacion":
            df = df.drop(columns=[c for c in ['Notes', 'Goalkeeper', 'Attendance'] if c in df.columns])
        
        df = df.rename(columns=TRADUCCIONES)
        return df.dropna(how='all')
    except Exception as e:
        return None

# ────────────────────────────────────────────────
# INTERFAZ
# ────────────────────────────────────────────────
st.markdown('<div style="text-align:center; margin-bottom:20px;"><img src="https://i.postimg.cc/C516P7F5/33.png" width="300"></div>', unsafe_allow_html=True)

tab_objects = st.tabs(list(LIGAS.values()))

for i, (code, nombre_pantalla) in enumerate(LIGAS.items()):
    with tab_objects[i]:
        archivo_sufijo = MAPEO_ARCHIVOS.get(nombre_pantalla)
        if f"show_{code}" not in st.session_state:
            st.session_state[f"show_{code}"] = None

        col1, col2, col3 = st.columns(3)
        if col1.button(f"🏆 Clasificación", key=f"btn_clas_{code}"):
            st.session_state[f"show_{code}"] = "clas"
        if col2.button(f"📊 Stats Generales", key=f"btn_stats_{code}"):
            st.session_state[f"show_{code}"] = "stats"
        if col3.button(f"📅 Ver Fixture", key=f"btn_fix_{code}"):
            st.session_state[f"show_{code}"] = "fix"

        st.divider()
        view = st.session_state[f"show_{code}"]

        if view == "stats":
            df_s = cargar_excel(f"RESUMEN_STATS_{archivo_sufijo}.xlsx", tipo="stats")
            if df_s is not None:
                styler_s = df_s.style.hide(axis='index')
                
                # Aplicar semáforo a xG si existe
                if 'xG' in df_s.columns:
                    df_s['xG'] = pd.to_numeric(df_s['xG'], errors='coerce')
                    m_min, m_max = df_s['xG'].min(), df_s['xG'].max()
                    styler_s = styler_s.applymap(lambda x: color_xg_celda(x, m_min, m_max), subset=['xG'])
                
                # Renderizar con escape=False para que el HTML de la barra funcione
                st.markdown(f'<div class="table-scroll">{styler_s.to_html(escape=False)}</div>', unsafe_allow_html=True)
            else: st.error("Archivo no disponible.")

        elif view == "clas":
            df_c = cargar_excel(f"CLASIFICACION_LIGA_{archivo_sufijo}.xlsx", tipo="clasificacion")
            if df_c is not None:
                if 'ÚLTIMOS 5' in df_c.columns: df_c['ÚLTIMOS 5'] = df_c['ÚLTIMOS 5'].apply(formatear_last_5)
                st.markdown(f'<div class="table-scroll">{df_c.style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

        elif view == "fix":
            df_f = cargar_excel(f"CARTELERA_PROXIMOS_{archivo_sufijo}.xlsx", tipo="fixture")
            if df_f is not None:
                st.markdown(f'<div class="table-scroll">{df_f.style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)
