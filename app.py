import streamlit as st
import requests

st.title("Prueba TheSportsDB Gratis: Próximos Partidos Premier League")

# Endpoint público de TheSportsDB (gratis)
BASE_URL = "https://www.thesportsdb.com/api/v1/json/123"

# 1️⃣ Obtener equipos de la Premier League
league_name = "English Premier League"
url_teams = f"{BASE_URL}/search_all_teams.php?l={league_name}"
r = requests.get(url_teams)

if r.status_code != 200:
    st.error(f"Error al cargar equipos: {r.status_code}")
else:
    teams = r.json().get("teams", [])
    st.write(f"Equipos encontrados en {league_name}: {len(teams)}")

    all_fixtures = []

    # 2️⃣ Obtener próximos partidos de cada equipo
    for team in teams:
        team_id = team["idTeam"]
        team_name = team["strTeam"]

        url_next = f"{BASE_URL}/eventsnext.php?id={team_id}"
        r2 = requests.get(url_next)
        if r2.status_code == 200:
            events = r2.json().get("events", [])
            for e in events:
                date = e.get("dateEvent")
                time = e.get("strTime")
                home = e.get("strHomeTeam")
                away = e.get("strAwayTeam")
                all_fixtures.append((date, time, home, away))

    # 3️⃣ Mostrar resultados
    if all_fixtures:
        st.write("Próximos partidos encontrados:")
        for f in all_fixtures:
            st.write(f"{f[0]} {f[1]} — {f[2]} vs {f[3]}")
    else:
        st.warning("No se encontraron próximos partidos.")
