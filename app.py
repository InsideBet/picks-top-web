import streamlit as st
import requests
from datetime import datetime, timedelta

API_KEY_AF = st.secrets["API_KEY_AF"]
HEADERS_AF = {"x-apisports-key": API_KEY_AF}
BASE_URL_AF = "https://v3.football.api-sports.io"

# Liga de prueba: Premier League
LEAGUE_ID = 39
DIAS_FUTUROS = 2

st.title("Prueba API-Football: Premier League")

# ────────────────────────────────────────────────
# Traer fixtures próximos
# ────────────────────────────────────────────────
from_date = datetime.now().strftime("%Y-%m-%d")
to_date = (datetime.now() + timedelta(days=DIAS_FUTUROS)).strftime("%Y-%m-%d")

url = f"{BASE_URL_AF}/fixtures"
params = {
    "league": LEAGUE_ID,
    "season": 2026,  # ajustá si es necesario
    "from": from_date,
    "to": to_date
}

r = requests.get(url, headers=HEADERS_AF, params=params, timeout=10)
if r.status_code != 200:
    st.error(f"Error API: {r.status_code}")
else:
    fixtures = r.json().get("response", [])
    st.write(f"Partidos encontrados: {len(fixtures)}")
    for f in fixtures[:5]:  # mostrar solo primeros 5 partidos
        home = f["teams"]["home"]["name"]
        away = f["teams"]["away"]["name"]
        fecha = f["fixture"]["date"]
        st.write(f"{fecha}: {home} vs {away}")
