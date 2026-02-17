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

# API Football
API_KEY_AF = st.secrets["API_KEY_AF"]  # Tu key de API-Football
BASE_URL_AF = "https://v3.football.api-sports.io"

HEADERS_AF = {"x-apisports-key": API_KEY_AF}

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

# Mapa de IDs de API-Football (Free plan)
# Asegurate que los IDs coincidan con la API
LIGAS_AF_ID = {
    "CL": 2,
    "PL": 39,
    "PD": 140,
    "SA": 135,
    "FL1": 61,
    "BL1": 78,
    "PPL": 94,
    "DED": 88,
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

DIAS_FUTUROS = 7

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
# FUNCIONES API
# ────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def cargar_fixtures_af(league_id):
    """Trae fixtures próximos de la API-Football"""
    from_date = datetime.now().strftime("%Y-%m-%d")
    to_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    url = f"{BASE_URL_AF}/fixtures"
    params = {
        "league": league_id,
        "season": 2026,  # ajustá a temporada actual
        "from": from_date,
        "to": to_date
    }

    r = requests.get(url, headers=HEADERS_AF, params=params, timeout=10)
    if r.status_code != 200:
        return [], f"Error {r.status_code}"
    return r.json().get("response", []), None


@st.cache_data(ttl=3600)
def get_odds_af(fixture_id):
    """Obtiene odds 1X2, Over/Under, BTTS"""
    url = f"{BASE_URL_AF}/odds"
    params = {
        "fixture": fixture_id,
        "bookmaker": 6  # free plan: select one bookmaker (ej. Bet365 id=6)
    }
    r = requests.get(url, headers=HEADERS_AF, params=params, timeout=10)
    if r.status_code != 200:
        return {}
    data = r.json().get("response", [])
    if not data:
        return {}
    markets = data[0].get("bookmakers", [{}])[0].get("bets", [])
    odds_dict = {}
    for m in markets:
        name = m.get("name")
        values = m.get("values", [])
        if values:
            if name == "Match Winner":
                odds_dict["1X2"] = {v["value"]: v["odd"] for v in values}
            elif name == "Over/Under 2.5":
                odds_dict["O/U 2.5"] = {v["value"]: v["odd"] for v in values}
            elif name == "Both Teams To Score":
                odds_dict["BTTS"] = {v["value"]: v["odd"] for v in values}
    return odds_dict


@st.cache_data(ttl=3600)
def get_statistics_af(fixture_id):
    """Obtiene corners y tarjetas"""
    url = f"{BASE_URL_AF}/fixtures/statistics"
    params = {"fixture": fixture_id}
    r = requests.get(url, headers=HEADERS_AF, params=params, timeout=10)
    if r.status_code != 200:
        return {}
    stats = r.json().get("response", [])
    if not stats:
        return {}
    result = {}
    for s in stats:
        team = s.get("team", {}).get("name")
        for st in s.get("statistics", []):
            if st.get("type") == "Corner":
                result[f"Corners {team}"] = st.get("value")
            if st.get("type") == "Yellow Card":
                result[f"Yellow {team}"] = st.get("value")
            if st.get("type") == "Red Card":
                result[f"Red {team}"] = st.get("value")
    return result

# ────────────────────────────────────────────────
# PROCESAMIENTO
# ────────────────────────────────────────────────
def procesar_fixtures(fixtures):
    datos = []
    for f in fixtures:
        fixture_id = f["fixture"]["id"]
        home = f["teams"]["home"]
        away = f["teams"]["away"]

        fecha = f["fixture"]["date"][:10]
        hora = f["fixture"]["date"][11:16]
        partido = f"{home['name']} vs {away['name']}"

        # Odds
        odds = get_odds_af(fixture_id)
        odds_1X2 = odds.get("1X2", {})
        odds_OU = odds.get("O/U 2.5", {})
        odds_BTTS = odds.get("BTTS", {})

        # Stats
        stats = get_statistics_af(fixture_id)
        corners_home = stats.get(f"Corners {home['name']}", "N/A")
        corners_away = stats.get(f"Corners {away['name']}", "N/A")
        yellow_home = stats.get(f"Yellow {home['name']}", "N/A")
        yellow_away = stats.get(f"Yellow {away['name']}", "N/A")
        red_home = stats.get(f"Red {home['name']}", "N/A")
        red_away = stats.get(f"Red {away['name']}", "N/A")

        # Picks
        pct_btts = 50  # como antes, podés reemplazar con tu fórmula
        avg_goles = 2  # ejemplo, podés calcular real si querés
        score = round(avg_goles * (pct_btts/100) * 2.5,1)
        pick_btts = "Yes" if pct_btts > 65 else "No"
        pick_over = "Over 2.5" if avg_goles > 2.5 else "Under 2.5"
        top_pick = pick_btts if pct_btts > 70 else pick_over

        datos.append({
            "Fecha 📅": fecha,
            "Hora ⏱️": hora,
            "Partido 🆚": partido,
            "1X2 Odds": odds_1X2 or "N/A",
            "O/U 2.5 Odds": odds_OU or "N/A",
            "BTTS Odds": odds_BTTS or "N/A",
            "Corners Home": corners_home,
            "Corners Away": corners_away,
            "Yellow Home": yellow_home,
            "Yellow Away": yellow_away,
            "Red Home": red_home,
            "Red Away": red_away,
            "BTTS ⚽": pick_btts,
            "O/U 2.5 ⚽": pick_over,
            "Top Pick 🔥": top_pick,
            "Score": score
        })
    return pd.DataFrame(datos)

# ────────────────────────────────────────────────
# INTERFAZ STREAMLIT
# ────────────────────────────────────────────────
tabs = st.tabs(list(LIGAS.values()))

for tab, (code, nombre) in zip(tabs, LIGAS.items()):
    with tab:
        st.markdown(f"### {nombre}")
        st.image(BANDERAS[code], width=60)

        fixtures, error = cargar_fixtures_af(LIGAS_AF_ID[code])
        if error:
            st.error(error)
            continue

        if not fixtures:
            st.warning("No hay partidos programados en el rango seleccionado.")
            continue

        df = procesar_fixtures(fixtures)
        df = df.sort_values("Score", ascending=False)

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
