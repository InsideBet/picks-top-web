import streamlit as st
import pandas as pd
import numpy as np

# ────────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ────────────────────────────────────────────────
st.set_page_config(page_title="InsideBet - Pro Suite", layout="wide")

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

# ────────────────────────────────────────────────
# FUNCIONES VISUALES (BADGES Y BARRAS)
# ────────────────────────────────────────────────

def formatear_xg_badge(val, label_only=False):
    try:
        num = float(val)
        if num > 2.50: label, color = "+2.5", "#137031"
        elif num > 1.50: label, color = "+1.5", "#137031"
        else: label, color = "+0.5", "#821f1f"
        
        if label_only: return label
        return f'<div style="display:flex;justify-content:center;"><span style="background-color:{color};color:white;padding:4px 10px;border-radius:6px;font-weight:bold;font-size:12px;min-width:45px;text-align:center;">{label}</span></div>'
    except: return val

def html_barra_posesion(valor):
    try:
        num = float(str(valor).replace('%',''))
        p = min(max(int(round(num if num > 1 else num*100)), 0), 100)
        return f'<div class="bar-container"><div class="bar-bg"><div class="bar-fill" style="width:{p}%;"></div></div><div class="bar-text">{p}%</div></div>'
    except: return valor

def formatear_last_5(valor):
    if pd.isna(valor): return ""
    letras = list(str(valor).upper().replace(" ", ""))[:5]
    html = '<div class="forma-container">'
    for l in letras:
        clase = "win" if l == 'W' else "loss" if l == 'L' else "draw" if l == 'D' else ""
        html += f'<span class="forma-box {clase}">{l.replace("W","G").replace("L","P").replace("D","E")}</span>'
    return html + '</div>'

# ────────────────────────────────────────────────
# LÓGICA DE CARGA Y FILTROS
# ────────────────────────────────────────────────

@st.cache_data(ttl=300)
def cargar_datos(liga_nombre, tipo):
    archivo = MAPEO_ARCHIVOS.get(liga_nombre)
    url = f"{BASE_URL}/RESUMEN_STATS_{archivo}.xlsx" if tipo == "stats" else f"{BASE_URL}/CLASIFICACION_LIGA_{archivo}.xlsx"
    try:
        df = pd.read_excel(url)
        # Limpieza de xG en columna Q
        if tipo == "stats" and len(df.columns) >= 17:
            df = df.rename(columns={df.columns[16]: 'xG'})
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return None

# ────────────────────────────────────────────────
# ESTILOS CSS
# ────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e5e7eb; }
    .table-scroll { width: 100%; max-height: 500px; overflow: auto; border: 1px solid #374151; border-radius: 8px; }
    th { position: sticky; top: 0; background-color: #1f2937 !important; color: white; padding: 12px; border: 1px solid #374151; text-align: center !important; }
    td { padding: 10px; border: 1px solid #374151; text-align: center !important; white-space: nowrap; }
    
    /* Hot Picks Card */
    .hot-card { background: linear-gradient(135deg, #821f1f 0%, #1f2937 100%); border-radius: 12px; padding: 15px; border-left: 5px solid #ff1800; margin-bottom: 10px; }
    
    /* Bar & Shapes */
    .bar-container { display: flex; align-items: center; gap: 8px; width: 120px; margin: 0 auto; }
    .bar-bg { background: #2d3139; border-radius: 10px; flex-grow: 1; height: 6px; overflow: hidden; }
    .bar-fill { background: #ff4b4b; height: 100%; }
    .bar-text { font-size: 11px; font-weight: bold; }
    .forma-container { display: flex; justify-content: center; gap: 3px; }
    .forma-box { width: 20px; height: 20px; line-height: 20px; text-align: center; border-radius: 3px; font-size: 10px; font-weight: bold; color: white; }
    .win { background: #137031; } .loss { background: #821f1f; } .draw { background: #82711f; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# INTERFAZ PRINCIPAL
# ────────────────────────────────────────────────
st.markdown('<div style="text-align:center;"><img src="https://i.postimg.cc/C516P7F5/33.png" width="250"></div>', unsafe_allow_html=True)

# 1. SECCIÓN HOT PICKS (Punto 1)
st.subheader("🔥 Algoritmo Hot Picks (Basado en xG)")
col_hp1, col_hp2, col_hp3 = st.columns(3)

# Simulación de detección automática (Se puede automatizar recorriendo todos los Excel)
with col_hp1:
    st.markdown('<div class="hot-card"><b>OVER 2.5</b><br>Manchester City<br><small>xG: 2.85 | Rachas GGG</small></div>', unsafe_allow_html=True)
with col_hp2:
    st.markdown('<div class="hot-card"><b>BTTS (Ambos Marcan)</b><br>Real Madrid vs Barça<br><small>xG Combinado: 4.10</small></div>', unsafe_allow_html=True)
with col_hp3:
    st.markdown('<div class="hot-card" style="border-left-color:#137031"><b>VALOR SEGURO</b><br>Bayern Munich<br><small>Posesión: 68%</small></div>', unsafe_allow_html=True)

st.divider()

# TABS DE LIGAS
tab_objs = st.tabs(list(LIGAS.values()))

for idx, (cod, nom) in enumerate(LIGAS.items()):
    with tab_objs[idx]:
        df_stats = cargar_datos(nom, "stats")
        df_clas = cargar_datos(nom, "clas")
        
        # 2. COMPARADOR H2H (Punto 2)
        if df_stats is not None:
            with st.expander("⚔️ Comparador H2H (Cara a Cara)"):
                c_h2h1, c_h2h2 = st.columns(2)
                eq1 = c_h2h1.selectbox("Equipo A (Local)", df_stats['Squad'].unique(), key=f"e1_{cod}")
                eq2 = c_h2h2.selectbox("Equipo B (Visitante)", df_stats['Squad'].unique(), key=f"e2_{cod}")
                
                if eq1 and eq2:
                    d1 = df_stats[df_stats['Squad'] == eq1].iloc[0]
                    d2 = df_stats[df_stats['Squad'] == eq2].iloc[0]
                    
                    st.markdown(f"""
                    <table style="width:100%; color:white; text-align:center; background:#1f2937; border-radius:10px;">
                        <tr><th>{eq1}</th><th>Métrica</th><th>{eq2}</th></tr>
                        <tr><td>{d1.get('Poss','-')}</td><td>Posesión</td><td>{d2.get('Poss','-')}</td></tr>
                        <tr><td>{d1.get('xG','-')}</td><td>xG</td><td>{d2.get('xG','-')}</td></tr>
                        <tr><td>{d1.get('CrdY','-')}</td><td>Amarillas</td><td>{d2.get('CrdY','-')}</td></tr>
                    </table>
                    """, unsafe_allow_html=True)

        # 3. FILTROS DE MERCADO (Punto 3)
        st.write("### 📊 Panel de Análisis")
        m1, m2, m3, m4 = st.columns(4)
        mercado = "General"
        if m1.button("🏆 Tabla Real", key=f"btn_t_{cod}"): mercado = "Clasificacion"
        if m2.button("⚽ Mercado Goles (xG)", key=f"btn_g_{cod}"): mercado = "Goles"
        if m3.button("🟨 Tarjetas / Faltas", key=f"btn_c_{cod}"): mercado = "Cards"
        if m4.button("🎮 Posesión / Control", key=f"btn_p_{cod}"): mercado = "Control"

        # Mostrar tablas según mercado
        if mercado == "Clasificacion" and df_clas is not None:
            df_view = df_clas.copy()
            if 'Last 5' in df_view.columns: df_view['Last 5'] = df_view['Last 5'].apply(formatear_last_5)
            st.markdown(f'<div class="table-scroll">{df_view.to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)
            
        elif df_stats is not None:
            df_view = df_stats.copy()
            
            # Tendencia (Punto 4: Sparkline visual simple con flechas/iconos)
            if 'xG' in df_view.columns:
                df_view['Tendencia'] = df_view['xG'].apply(lambda x: "📈" if float(x) > 1.8 else "📉" if float(x) < 1.2 else "📊")
                df_view['xG'] = df_view['xG'].apply(formatear_xg_badge)
            
            if 'Poss' in df_view.columns:
                df_view['Poss'] = df_view['Poss'].apply(html_barra_posesion)
            
            # Selección de columnas por mercado
            if mercado == "Goles":
                cols = ['Squad', 'MP', 'Gls', 'xG', 'Tendencia']
            elif mercado == "Cards":
                cols = ['Squad', 'MP', 'CrdY', 'CrdR']
            elif mercado == "Control":
                cols = ['Squad', 'Poss', 'Ast']
            else:
                cols = ['Squad', 'MP', 'Poss', 'Gls', 'xG']
                
            df_view = df_view[[c for c in cols if c in df_view.columns]]
            st.markdown(f'<div class="table-scroll">{df_view.to_html(escape=False, index=False)}</div>', unsafe_allow_html=True)
