import streamlit as st
import requests
from datetime import datetime, timedelta

# ────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────
API_KEY = st.secrets["SPORTDB_KEY"]  # tu key de SportDB
BASE_URL = "https://sportdb.dev/api/v1/json"

# Liga de prueba: Premier League (cambia el ID si querés otra liga)
LEAGUE_ID = 4328  # Premier League según SportDB
DIAS_FUTUROS = 7

st.title("Prueba SportDB: Fixtures Próximos")

# ────────────────────────────────────────────────
# Fechas
# ────────────────────────────────────────────────
from_date = datetime.now().strftime("%Y-%m-%d")
to_date = (datetime.now() + timedelta(days=DIAS_FUTUROS)).strftime("%Y-%m-%d")

# ────────────────────────────────────────────────
# Llamada API
# ────────────────────────────────────────────────
url = f"{BASE_URL}/{API_KEY}/eventsnextleague.php?id={LEAGUE_ID}"

r = requests.get(url)
if r.status_code != 200:
    st.error(f"Error API: {r.status_code}")
else:
    fixtures = r.json().get("events", [])
    st.write(f"Partidos próximos encontrados: {len(fixtures)}")

    if not fixtures:
        st.warning("No hay partidos programados en los próximos 7 días.")
    else:
        for f in fixtures:
            fecha = f.get("dateEvent")
            hora = f.get("strTime")
            home = f.get("strHomeTeam")
            away = f.get("strAwayTeam")
            st.write(f"{fecha} {hora} — {home} vs {away}")
