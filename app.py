import streamlit as st
import pandas as pd

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

BANDERAS = {
    "PL": "https://i.postimg.cc/7PcwYbk1/1.png", "PD": "https://i.postimg.cc/75d5mMQ2/8.png",
    "SA": "https://i.postimg.cc/mzxTFmpm/4.png", "BL1": "https://i.postimg.cc/5X09cYFn/3.png",
    "FL1": "https://i.postimg.cc/jnbqBMz2/2.png", "PPL": "https://i.postimg.cc/ZBr4P61R/5.png",
    "DED": "https://i.postimg.cc/tnkbwpqv/6.png", "CL": "https://i.postimg.cc/zb1V1DNy/7.png"
}

TRADUCCIONES = {
    'Rk': 'POS', 'Squad': 'EQUIPO', 'MP': 'PJ', 'W': 'G', 'D': 'E', 'L': 'P',
    'GF': 'GF', 'GA': 'GC', 'GD': 'DG', 'Pts': 'PTS', 'PTS': 'PTS',
    'Last 5': 'ÚLTIMOS 5'
}

# ────────────────────────────────────────────────
# ESTILO CSS (Cuadraditos y Tabla Limpia)
# ────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e5e7eb; }
    
    .forma-container {
        display: flex;
        justify-content: center;
        gap: 4px;
        min-width: 120px;
    }

    .forma-box {
        flex: 0 0 22px;
        height: 22px;
        line-height: 22px;
        text-align: center;
        border-radius: 4px;
        font-weight: bold;
        font-size: 11px;
        color: white;
    }
    
    .win { background-color: #137031; }
    .loss { background-color: #821f1f; }
    .draw { background-color: #82711f; }

    /* Tabla sin espacios extra a la izquierda */
    table { 
        width: 100%; 
        border-collapse: collapse; 
        color: #e5e7eb;
    }
    th { background-color: #1f2937; padding: 12px; border: 1px solid #374151; font-size: 13px; }
    td { padding: 10px; border: 1px solid #374151; font-size: 14px; text-align: center; }
    
    tr:hover { background-color: #21262d; }

    /* Estilo para la columna PTS (Color sólido más claro que el fondo) */
    .col-pts {
        background-color: #2d333b !important; /* Un gris azulado suave y sólido */
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# FUNCIONES
# ────────────────────────────────────────────────
def formatear_last_5(valor):
    if pd.isna(valor): return ""
    trad = {'W': 'G', 'L': 'P', 'D': 'E'}
    letras = list(str(valor).upper().replace(" ", ""))[:5]
    html_str = '<div class="forma-container">'
    for l in letras:
        clase = "win" if l == 'W' else "loss" if l == 'L' else "draw" if l == 'D' else ""
        letra_visual = trad.get(l, l)
        html_str += f'<span class="forma-box {clase}">{letra_visual}</span>'
    html_str += '</div>'
    return html_str

@st.cache_data(ttl=300)
def cargar_excel(ruta_archivo):
    url = f"{BASE_URL}/{ruta_archivo}"
    try:
        df = pd.read_excel(url)
        # Limpieza de columnas innecesarias
        cols_drop = ['Notes', 'Goalkeeper', 'Top Team Scorer', 'Attendance', 'Pts/MP', 'Pts/PJ']
        df = df.drop(columns=[c for c in cols_drop if c in df.columns])
        # Traducción de cabeceras
        df = df.rename(columns=TRADUCCIONES)
        return df.dropna(how='all')
    except:
        return None

# ────────────────────────────────────────────────
# INTERFAZ
# ────────────────────────────────────────────────
st.markdown('<div style="text-align:center; margin-bottom:20px;"><img src="https://i.postimg.cc/hPkSPNcT/Sin-titulo-2.png" width="280"></div>', unsafe_allow_html=True)

tab_objects = st.tabs(list(LIGAS.values()))

for i, (code, nombre_pantalla) in enumerate(LIGAS.items()):
    with tab_objects[i]:
        archivo_sufijo = MAPEO_ARCHIVOS.get(nombre_pantalla)
        
        # Botones de acción
        col1, col2, col3 = st.columns(3)
        with col1: btn_clasif = st.button(f"🏆 Clasificación", key=f"btn_clas_{code}")
        with col2: btn_stats = st.button(f"📊 Stats Generales", key=f"btn_stats_{code}")
        with col3: btn_fix = st.button(f"📅 Ver Fixture", key=f"btn_fix_{code}")

        df_para_lista = cargar_excel(f"RESUMEN_STATS_{archivo_sufijo}.xlsx")
        equipo_sel = st.selectbox("🔍 Analizar Equipo:", ["Seleccionar..."] + sorted([str(x) for x in df_para_lista['EQUIPO'].unique()]) if df_para_lista is not None else ["Seleccionar..."], key=f"sel_{code}")

        st.divider()

        if equipo_sel != "Seleccionar...":
            df_ind = cargar_excel(f"Ligas_Equipos/{equipo_sel.replace(' ', '_')}.xlsx")
            if df_ind is not None: st.dataframe(df_ind, use_container_width=True, hide_index=True)

        elif btn_clasif:
            df_c = cargar_excel(f"CLASIFICACION_LIGA_{archivo_sufijo}.xlsx")
            if df_c is not None:
                # 1. ELIMINAR EL ÍNDICE COMPLETAMENTE
                df_c = df_c.reset_index(drop=True)
                
                # 2. Formatear la columna de forma
                col_forma = 'ÚLTIMOS 5' if 'ÚLTIMOS 5' in df_c.columns else 'Last 5'
                if col_forma in df_c.columns:
                    df_c[col_forma] = df_c[col_forma].apply(formatear_last_5)
                
                # 3. Aplicar clase CSS a la columna PTS para el color sólido
                styler = df_c.style.set_table_styles({
                    'PTS': [{'selector': 'td', 'props': [('background-color', '#2d333b'), ('font-weight', 'bold')]}]
                }, overwrite=False)
                
                # 4. Renderizado HTML SIN ÍNDICE (index=False es vital aquí)
                html_tabla = df_c.style.set_td_classes(
                    pd.DataFrame([['col-pts' if col == 'PTS' else '' for col in df_c.columns] for _ in range(len(df_c))], 
                                 index=df_c.index, columns=df_c.columns)
                ).to_html(escape=False, index=False)
                
                st.markdown(html_tabla, unsafe_allow_html=True)
            else:
                st.error("Archivo no encontrado.")
