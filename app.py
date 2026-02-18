import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# ────────────────────────────────────────────────
# CONFIGURACIÓN
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="InsideBet",
    layout="wide"
)

# Ligas y banderas
LIGAS = {
    "CL": "UEFA Champions League",
    "PL": "Premier League",
    "PD": "La Liga",
    "SA": "Serie A",
    "FL1": "Ligue 1",
    "BL1": "Bundesliga",
    "PPL": "Primeira Liga",
    "DED": "Eredivisie",
}

BANDERAS = {
    "PL": "https://i.postimg.cc/7PcwYbk1/1.png",
    "PD": "https://i.postimg.cc/75d5mMQ2/8.png",
    "SA": "https://i.postimg.cc/mzxTFmpm/4.png",
    "FL1": "https://i.postimg.cc/jnbqBMz2/2.png",
    "BL1": "https://i.postimg.cc/5X09cYFn/3.png",
    "PPL": "https://i.postimg.cc/ZBr4P61R/5.png",
    "DED": "https://i.postimg.cc/tnkbwpqv/6.png",
    "CL": "https://i.postimg.cc/zb1V1DNy/7.png"
}

DIAS_FUTUROS = 7
THESPORTSDB_KEY = "1"  # Key pública TSDB

# ────────────────────────────────────────────────
# ESTILO STREAMLIT
# ────────────────────────────────────────────────
st.markdown("""
<style>
.stApp {
    background-color: #0e1117;
    color: #e5e7eb;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center; margin-top:15px; margin-bottom:20px;">
    <img src="https://i.postimg.cc/hPkSPNcT/Sin-titulo-2.png" width="280"><br>
    <p style="
        font-family: 'Montserrat', sans-serif;
        font-size:18px;
        font-weight:500;
        color:#e5e7eb;
        margin-top:10px;
    ">
       Partidos & Estadísticas
    </p>
</div>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# FUNCIONES TSDB
# ────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def cargar_fixtures_tsdb(liga_nombre):
    """Trae fixtures próximos de TheSportsDB"""
    url_teams = f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_KEY}/search_all_teams.php"
    params = {"l": liga_nombre}
    r = requests.get(url_teams, params=params, timeout=10)
    if r.status_code != 200:
        return [], f"Error TSDB {r.status_code}"
    teams = r.json().get("teams")
    if not teams:
        return [], "No se encontraron equipos en TSDB"
    fixtures = []
    for team in teams:
        team_id = team.get("idTeam")
        if not team_id:
            continue
        url_events = f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_KEY}/eventsnext.php"
        r2 = requests.get(url_events, params={"id": team_id}, timeout=10)
        if r2.status_code != 200:
            continue
        events = r2.json().get("events")
        if events:
            fixtures.extend(events)
    return fixtures, None

def procesar_fixtures_tsdb(fixtures):
    """Convierte fixtures TSDB a DataFrame"""
    datos = []
    for f in fixtures:
        home = f.get("strHomeTeam")
        away = f.get("strAwayTeam")
        fecha = f.get("dateEvent") or "N/A"
        hora = f.get("strTime") or "N/A"
        pct_btts = 50
        avg_goles = 2
        score = round(avg_goles * (pct_btts/100) * 2.5,1)
        pick_btts = "Yes" if pct_btts > 65 else "No"
        pick_over = "Over 2.5" if avg_goles > 2.5 else "Under 2.5"
        top_pick = pick_btts if pct_btts > 70 else pick_over
        datos.append({
            "Fecha 📅": fecha,
            "Hora ⏱️": hora,
            "Partido 🆚": f"{home} vs {away}",
            "1X2 Odds": "N/A",
            "O/U 2.5 Odds": "N/A",
            "BTTS Odds": "N/A",
            "Corners Home": "N/A",
            "Corners Away": "N/A",
            "Yellow Home": "N/A",
            "Yellow Away": "N/A",
            "Red Home": "N/A",
            "Red Away": "N/A",
            "BTTS ⚽": pick_btts,
            "O/U 2.5 ⚽": pick_over,
            "Top Pick 🔥": top_pick,
            "Score": score
        })
    return pd.DataFrame(datos)

# ────────────────────────────────────────────────
# INTERFAZ STREAMLIT
# ────────────────────────────────────────────────
tab_objects = st.tabs(list(LIGAS.values()))

for i, (code, nombre) in enumerate(LIGAS.items()):
    with tab_objects[i]:
        st.markdown(f"""
        <div style="display:flex; align-items:center; color:#e5e7eb; font-size:22px; font-weight:500; margin-bottom:10px;">
            <img src="{BANDERAS[code]}" width="30" style="vertical-align:middle; margin-right:10px;">
            <span>{nombre}</span>
        </div>
        """, unsafe_allow_html=True)

        # Traer fixtures de TSDB
        fixtures_tsdb, error_tsdb = cargar_fixtures_tsdb(nombre)
        if error_tsdb:
            st.error(f"TheSportsDB: {error_tsdb}")

        df_tsdb = procesar_fixtures_tsdb(fixtures_tsdb) if fixtures_tsdb else pd.DataFrame()

        if df_tsdb.empty:
            st.warning("No hay partidos programados en el rango seleccionado.")
        else:
            df = df_tsdb.sort_values("Score", ascending=False)
            st.dataframe(
                df,
                use_container_width=True,
                height=600,
                hide_index=True,
                column_config={
                    "Score": st.column_config.ProgressColumn(
                        "Score",
                        help="Nivel de confianza del pick",
                        min_value=0,
                        max_value=10,
                        format="%.1f"
                    ),
                }
            )
            st.success(f"{len(df)} partidos encontrados.")
