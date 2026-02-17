import streamlit as st
import requests
from datetime import datetime, timedelta

# ────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────
API_KEY_AF = st.secrets["API_KEY_AF"]
HEADERS_AF = {"x-apisports-key": API_KEY_AF}
BASE_URL_AF = "https://v3.football.api-sports.io"

# Liga de prueba: Champions League (ID API-Football)
LEAGUE_ID = 2
SEASON = 2025  # año de inicio de temporada 2025/26
DIAS_FUTUROS = 7

st.title("Prueba API-Football: Champions League")

# ────────────────────────────────────────────────
# Fechas para filtrar
# ────────────────────────────────────────────────
from_date = datetime.now().strftime("%Y-%m-%d")
to_date = (datetime.now() + timedelta(days=DIAS_FUTUROS)).strftime("%Y-%m-%d")

# ────────────────────────────────────────────────
# Traer fixtures próximos
# ────────────────────────────────────────────────
url_fixtures = f"{BASE_URL_AF}/fixtures"
params_fixtures = {
    "league": LEAGUE_ID,
    "season": SEASON,
    "from": from_date,
    "to": to_date
}

r = requests.get(url_fixtures, headers=HEADERS_AF, params=params_fixtures, timeout=10)

if r.status_code != 200:
    st.error(f"Error API: {r.status_code}")
else:
    fixtures = r.json().get("response", [])
    st.write(f"Partidos encontrados: {len(fixtures)}")

    if not fixtures:
        st.warning("No hay partidos programados en el rango seleccionado.")
    else:
        for f in fixtures[:5]:  # mostramos solo los primeros 5
            fixture_id = f["fixture"]["id"]
            home = f["teams"]["home"]["name"]
            away = f["teams"]["away"]["name"]
            fecha = f["fixture"]["date"][:16]

            st.write(f"{fecha}: {home} vs {away}")

            # ─── Odds 1X2, Over/Under 2.5, BTTS ───
            url_odds = f"{BASE_URL_AF}/odds"
            params_odds = {"fixture": fixture_id, "bookmaker": 6}  # Bet365 free
            r_odds = requests.get(url_odds, headers=HEADERS_AF, params=params_odds, timeout=10)

            odds_dict = {}
            if r_odds.status_code == 200:
                data_odds = r_odds.json().get("response", [])
                if data_odds:
                    markets = data_odds[0].get("bookmakers", [{}])[0].get("bets", [])
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
            st.write("Odds:", odds_dict if odds_dict else "N/A")

            # ─── Estadísticas: Corners y Tarjetas ───
            url_stats = f"{BASE_URL_AF}/fixtures/statistics"
            params_stats = {"fixture": fixture_id}
            r_stats = requests.get(url_stats, headers=HEADERS_AF, params=params_stats, timeout=10)

            stats_dict = {}
            if r_stats.status_code == 200:
                stats = r_stats.json().get("response", [])
                for s in stats:
                    team = s.get("team", {}).get("name")
                    for st_item in s.get("statistics", []):
                        if st_item.get("type") == "Corner":
                            stats_dict[f"Corners {team}"] = st_item.get("value")
                        if st_item.get("type") == "Yellow Card":
                            stats_dict[f"Yellow {team}"] = st_item.get("value")
                        if st_item.get("type") == "Red Card":
                            stats_dict[f"Red {team}"] = st_item.get("value")
            st.write("Estadísticas:", stats_dict if stats_dict else "N/A")
