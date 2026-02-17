import streamlit as st
import requests
from datetime import datetime, timedelta

# ────────────────────────────────────────────────
# CONFIGURACIÓN
# ────────────────────────────────────────────────
API_KEY = st.secrets["THESPORTSDB_KEY"]  # tu key de TheSportsDB
LEAGUE_ID = 4328  # Premier League
DIAS_FUTUROS = 7

st.title("Prueba TheSportsDB: Próximos Partidos")

# ────────────────────────────────────────────────
# Llamada a fixtures próximos
# ────────────────────────────────────────────────
url = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/eventsnextleague.php?id={LEAGUE_ID}"

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
            status = f.get("strStatus") or "Programado"
            st.write(f"{fecha} {hora} — {home} vs {away} | Estado: {status}")
