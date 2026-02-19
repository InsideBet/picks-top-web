import streamlit as st
import pandas as pd
import numpy as np

# ────────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
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
    "Bundesliga": "Bundesliga", "Ligue_1": "Ligue_1", "Primeira Liga": "Primeira_Liga",
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
# ALGORITMO HOT PICKS (Lógica de Scrapeo Interna)
# ────────────────────────────────────────────────

def obtener_hot_picks():
    """Analiza todas las ligas y devuelve los mejores picks basados en xG y Posesión."""
    picks = []
    for cod, nombre in LIGAS.items():
        archivo = MAPEO_ARCHIVOS.get(nombre)
        url = f"{BASE_URL}/RESUMEN_STATS_{archivo}.xlsx"
        try:
            df = pd.read_excel(url)
            # Extraer xG de columna Q (índice 16)
            if len(df.columns) >= 17:
                col_xg = df.columns[16]
                df['xG_val'] = pd.to_numeric(df[col_xg], errors='coerce')
                df['Poss_val'] = pd.to_numeric(df['Poss'].str.replace('%',''), errors='coerce')
                
                # Regla 1: Over 2.5 (xG alto)
                best_xg = df.nlargest(1, 'xG_val').iloc[0]
                if best_xg['xG_val'] > 2.0:
                    picks.append({
                        'tipo': '🔥 OVER 2.5',
                        'equipo': best_xg['Squad'],
                        'liga': nombre,
                        'dato': f"xG: {best_xg['xG_val']:.2f}"
                    })
                
                # Regla 2: Posesión dominante (Control)
                best_poss = df.nlargest(1, 'Poss_val').iloc[0]
                if best_poss['Poss_val'] > 60:
                    picks.append({
                        'tipo': '🎮 DOMINIO',
                        'equipo': best_poss['Squad'],
                        'liga': nombre,
                        'dato': f"Posesión: {best_poss['Poss_val']}%"
                    })
        except:
            continue
    return picks[:3] # Retornamos los 3 mejores

# ────────────────────────────────────────────────
# FUNCIONES DE PROCESAMIENTO VISUAL
# ────────────────────────────────────────────────

def formatear_xg_badge(val):
    try:
        num = float(val)
        if num > 2.50: label, color = "+2.5", "#137031"
        elif num > 1.50: label, color = "+1.5", "#137031"
        else: label, color = "+0.5", "#821f1f"
        return f'<div style="display:flex;justify-content:center;"><span style="background-color:{color};color:white;padding:4px 10px;border-radius:6px;font-weight:bold;font-size:12px;min-width:45px;text-align:center;">{label}</span></div>'
    except: return val

def html_barra_posesion(valor):
    try:
        clean_val = str(valor).replace('%', '').strip()
        num = float(clean_val)
        percent = int(round(num if num > 1 else num * 100))
        percent = min(max(percent, 0), 100)
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
        if tipo == "stats":
            if len(df.columns) >= 17:
                col_q = df.columns[16]
                df = df.rename(columns={col_q: 'xG'})
            df.columns = [str(c).strip() for c in df.columns]
            if 'xG' in df.columns: df['xG'] = df['xG'].apply(formatear_xg_badge)
            if 'Poss' in df.columns: df['Poss'] = df['Poss'].apply(html_barra_posesion)
            cols_ok = ['Squad', 'MP', 'Poss', 'Gls', 'Ast', 'CrdY', 'CrdR', 'xG']
            df = df[[c for c in cols_ok if c in df.columns]]
        elif tipo == "clasificacion":
            drop_c = ['Notes', 'Goalkeeper', 'Top Team Scorer', 'Attendance', 'Pts/MP', 'Pts/PJ']
            df = df.drop(columns=[c for c in drop_c if c in df.columns])
        elif tipo == "fixture":
            drop_f = ['Day', 'Score', 'Referee', 'Match Report', 'Notes', 'Attendance', 'Wk']
            df = df.drop(columns=[c for c in drop_f if c in df.columns])
        df = df.rename(columns=TRADUCCIONES)
        return df.dropna(how='all')
    except: return None

# ────────────────────────────────────────────────
# ESTILOS CSS
# ────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e5e7eb; }
    .table-scroll { width: 100%; max-height: 450px; overflow: auto; border: 1px solid #374151; border-radius: 8px; margin-bottom: 20px; }
    th { position: sticky; top: 0; background-color: #1f2937 !important; color: white; padding: 12px; border: 1px solid #374151; text-align: center !important; }
    td { padding: 10px; border: 1px solid #374151; text-align: center !important; white-space: nowrap; }
    .bar-container { display: flex; align-items: center; justify-content: flex-start; gap: 8px; width: 140px; margin: 0 auto; }
    .bar-bg { background-color: #2d3139; border-radius: 10px; flex-grow: 1; height: 7px; overflow: hidden; }
    .bar-fill { background-color: #ff4b4b; height: 100%; border-radius: 10px; }
    .bar-text { font-size: 12px; font-weight: bold; min-width: 32px; text-align: right; }
    .forma-container { display: flex; justify-content: center; gap: 4px; }
    .forma-box { width: 22px; height: 22px; line-height: 22px; text-align: center; border-radius: 4px; font-weight: bold; font-size: 11px; color: white; }
    .win { background-color: #137031; } .loss { background-color: #821f1f; } .draw { background-color: #82711f; }
    
    /* Hot Pick Card Style */
    .hot-pick-card {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        border: 1px solid #374151;
        border-left: 5px solid #ff1800;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# LOGO Y ALGORITMO HOT PICKS
# ────────────────────────────────────────────────
st.markdown('<div style="text-align:center; margin-bottom:20px;"><img src="https://i.postimg.cc/C516P7F5/33.png" width="300"></div>', unsafe_allow_html=True)

st.subheader("🔥 Algoritmo Hot Picks")
picks = obtener_hot_picks()
if picks:
    cols = st.columns(len(picks))
    for i, p in enumerate(picks):
        with cols[i]:
            st.markdown(f"""
            <div class="hot-pick-card">
                <span style="color:#ff1800; font-weight:bold; font-size:14px;">{p['tipo']}</span><br>
                <span style="font-size:18px; font-weight:bold;">{p['equipo']}</span><br>
                <span style="color:#9ca3af; font-size:12px;">{p['liga']} • {p['dato']}</span>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("Buscando las mejores oportunidades en los datos...")

st.divider()

# ────────────────────────────────────────────────
# TABS Y TABLAS
# ────────────────────────────────────────────────
tab_objects = st.tabs(list(LIGAS.values()))

for i, (code, nombre_pantalla) in enumerate(LIGAS.items()):
    with tab_objects[i]:
        archivo_sufijo = MAPEO_ARCHIVOS.get(nombre_pantalla)
        if f"show_{code}" not in st.session_state: st.session_state[f"show_{code}"] = None

        c1, c2, c3 = st.columns(3)
        if c1.button(f"🏆 Clasificación", key=f"c_{code}"): st.session_state[f"show_{code}"] = "clas"
        if c2.button(f"📊 Stats Generales", key=f"s_{code}"): st.session_state[f"show_{code}"] = "stats"
        if c3.button(f"📅 Ver Fixture", key=f"f_{code}"): st.session_state[f"show_{code}"] = "fix"

        st.divider()
        view = st.session_state[f"show_{code}"]

        if view == "stats":
            df = cargar_excel(f"RESUMEN_STATS_{archivo_sufijo}.xlsx", tipo="stats")
            if df is not None:
                html_table = df.style.hide(axis='index').to_html(escape=False)
                st.markdown(f'<div class="table-scroll">{html_table}</div>', unsafe_allow_html=True)

        elif view == "clas":
            df = cargar_excel(f"CLASIFICACION_LIGA_{archivo_sufijo}.xlsx", tipo="clasificacion")
            if df is not None:
                if 'ÚLTIMOS 5' in df.columns: df['ÚLTIMOS 5'] = df['ÚLTIMOS 5'].apply(formatear_last_5)
                st.markdown(f'<div class="table-scroll">{df.style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)

        elif view == "fix":
            df = cargar_excel(f"CARTELERA_PROXIMOS_{archivo_sufijo}.xlsx", tipo="fixture")
            if df is not None:
                st.markdown(f'<div class="table-scroll">{df.style.hide(axis="index").to_html(escape=False)}</div>', unsafe_allow_html=True)
