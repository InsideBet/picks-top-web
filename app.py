import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# ────────────────────────────────────────────────
# CONFIGURACIÓN
# ────────────────────────────────────────────────
st.set_page_config(page_title="InsideBet", layout="wide")

API_FOOTBALL_KEY = st.secrets["API_FOOTBALL_KEY"]
BASE_URL_FD = "https://api.football-data.org/v4"
BASE_URL_AF = "https://v3.football.api-sports.io"

HEADERS_FD = {"X-Auth-Token": st.secrets["API_KEY"]}
HEADERS_AF = {"x-apisports-key": API_FOOTBALL_KEY}

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
    "PL": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Flag_of_the_United_Kingdom_%281-2%29.svg/1920px-Flag_of_the_United_Kingdom_%281-2%29.svg.png",
    "PD": "https://upload.wikimedia.org/wikipedia/en/thumb/9/9a/Flag_of_Spain.svg/960px-Flag_of_Spain.svg.png",
    "SA": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/03/Flag_of_Italy.svg/250px-Flag_of_Italy.svg.png",
    "FL1": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Flag_of_France.svg/1280px-Flag_of_France.svg.png",
    "BL1": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Flag_of_Germany.svg/1280px-Flag_of_Germany.svg.png",
    "PPL": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Flag_of_Portugal_%28official%29.svg/1280px-Flag_of_Portugal_%28official%29.svg.png",
    "DED": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Flag_of_the_Netherlands.svg/1280px-Flag_of_the_Netherlands.svg.png",
    "CL": "https://i.postimg.cc/28pJqYLN/UEFA-Champions-League-logo.png"
}

dias_futuros = 2

# Tema dark
st.markdown("""
<style>
.stApp { background-color: #0e1117; color: #e5e7eb; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# FUNCIONES
# ────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def cargar_partidos_liga(code):
    today = datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=dias_futuros)).strftime('%Y-%m-%d')
    url = f"{BASE_URL_FD}/competitions/{code}/matches"
    params = {"dateFrom": today, "dateTo": end_date}

    try:
        r = requests.get(url, headers=HEADERS_FD, params=params, timeout=10)
        if r.status_code != 200:
            return [], f"Error FD {r.status_code}"
        return r.json().get("matches", []), None
    except Exception as e:
        return [], f"Error conexión FD: {str(e)}"

@st.cache_data(ttl=3600)
def get_stats_historicos(equipo_id, limite=5):
    url = f"{BASE_URL_FD}/teams/{equipo_id}/matches"
    params = {"status": "FINISHED", "limit": limite}
    try:
        r = requests.get(url, headers=HEADERS_FD, params=params, timeout=10)
        if r.status_code != 200:
            return {"avg_goles": 0, "pct_btts": 0}
        matches = r.json().get("matches", [])
        total_goles = sum((m.get("score", {}).get("fullTime", {}).get("home") or 0) +
                          (m.get("score", {}).get("fullTime", {}).get("away") or 0)
                          for m in matches)
        btts_count = sum(1 for m in matches if (m.get("score", {}).get("fullTime", {}).get("home") or 0) > 0
                                                and (m.get("score", {}).get("fullTime", {}).get("away") or 0) > 0)
        n = len(matches)
        return {"avg_goles": total_goles / n if n else 0,
                "pct_btts": (btts_count / n * 100) if n else 0}
    except Exception:
        return {"avg_goles": 0, "pct_btts": 0}

# ───────── API-FOOTBALL ─────────
@st.cache_data(ttl=3600)
def cargar_api_football_fixture(team_home, team_away, season=2025):
    # Busca el fixture exacto por equipos
    url = f"{BASE_URL_AF}/fixtures"
    params = {"team": team_home, "season": season, "next": 10}
    try:
        r = requests.get(url, headers=HEADERS_AF, params=params, timeout=10)
        if r.status_code != 200:
            return None
        response = r.json().get("response", [])
        # Filtra partido exacto por equipo local/visitante
        for f in response:
            h = f["teams"]["home"]["id"]
            a = f["teams"]["away"]["id"]
            if str(h) == str(team_home) and str(a) == str(team_away):
                return f
        return None
    except Exception:
        return None

# ───────── PROCESAR PARTIDOS ─────────
def procesar_partidos(matches):
    datos = []
    stats_cache = {}

    for p in matches:
        home = p["homeTeam"]
        away = p["awayTeam"]
        home_name = home.get("shortName") or home.get("name")
        away_name = away.get("shortName") or away.get("name")
        fecha = p["utcDate"][:10]
        hora = p["utcDate"][11:16]
        home_id = home["id"]
        away_id = away["id"]

        # Estadísticas históricas
        if home_id not in stats_cache:
            stats_cache[home_id] = get_stats_historicos(home_id)
        if away_id not in stats_cache:
            stats_cache[away_id] = get_stats_historicos(away_id)

        stats_home = stats_cache[home_id]
        stats_away = stats_cache[away_id]

        avg_goles = (stats_home["avg_goles"] + stats_away["avg_goles"]) / 2
        pct_btts = (stats_home["pct_btts"] + stats_away["pct_btts"]) / 2

        # Score
        score = round(avg_goles * (pct_btts / 100) * 2.5, 1)

        # Picks básicos
        pick_btts = "Yes" if pct_btts > 65 else "No"
        pick_over = "Over 2.5" if avg_goles > 2.5 else "Under 2.5"
        top_pick = pick_btts if pct_btts > 70 else pick_over

        # ───────── Datos API-Football (si disponible) ─────────
        af_data = cargar_api_football_fixture(home_id, away_id)
        prob_1x2 = None
        if af_data and "predictions" in af_data and af_data["predictions"]:
            pred = af_data["predictions"][0]
            prob_1x2 = f"{pred['win']['home']}% / {pred['win']['draw']}% / {pred['win']['away']}%"

        datos.append({
            "Fecha 📅": fecha,
            "Hora ⏱️": hora,
            "Partido 🆚": f"{home_name} vs {away_name}",
            "BTTS ⚽": f"{pick_btts} ({round(pct_btts)}%)",
            "O/U 2.5 ⚽": pick_over,
            "Top Pick 🔥": top_pick,
            "Score": score,
            "Prob 1X2 %": prob_1x2 or "N/A"
        })

    return pd.DataFrame(datos)

# ────────────────────────────────────────────────
# INTERFAZ
# ────────────────────────────────────────────────
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

tabs = st.tabs(list(LIGAS.values()))
for tab, (code, nombre) in zip(tabs, LIGAS.items()):
    with tab:
        st.markdown(f"### {nombre}")
        st.image(BANDERAS[code], width=60)
        matches, error = cargar_partidos_liga(code)

        if error:
            st.error(error)
        elif matches:
            df = procesar_partidos(matches)
            if df.empty:
                st.warning("No hay datos disponibles.")
            else:
                df = df.sort_values("Score", ascending=False)
                st.dataframe(
                    df,
                    use_container_width=True,
                    height=600,
                    column_config={
                        "Score": st.column_config.ProgressColumn(
                            "Score",
                            help="Nivel de confianza del pick",
                            min_value=0,
                            max_value=10,
                            format="%.1f",
                        ),
                    },
                    hide_index=True
                )
                st.success(f"{len(df)} partidos encontrados.")
        else:
            st.warning("No hay partidos programados en el rango seleccionado.")
