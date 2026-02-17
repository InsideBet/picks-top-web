import streamlit as st
import requests

# ────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────
API_KEY = st.secrets["SPORTSDB_KEY"]  # tu key
st.title("Prueba TheSportsDB: Fixtures Próximos")

# ────────────────────────────────────────────────
# Paso 1: Obtener ligas disponibles
# ────────────────────────────────────────────────
url_leagues = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/all_leagues.php"
r = requests.get(url_leagues)

if r.status_code != 200:
    st.error(f"Error al cargar ligas: {r.status_code}")
else:
    leagues = r.json().get("leagues", [])
    if not leagues:
        st.warning("No hay ligas disponibles para tu key.")
    else:
        # Creamos un diccionario {nombre: id} de ligas
        league_dict = {l['strLeague']: l['idLeague'] for l in leagues}
        league_name = st.selectbox("Selecciona una liga:", list(league_dict.keys()))
        league_id = league_dict[league_name]

        st.write(f"ID seleccionado: {league_id}")

        # ────────────────────────────────────────────────
        # Paso 2: Obtener próximos fixtures
        # ────────────────────────────────────────────────
        url_fixtures = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/eventsnextleague.php?id={league_id}"
        r2 = requests.get(url_fixtures)

        if r2.status_code != 200:
            st.error(f"Error al cargar fixtures: {r2.status_code}")
        else:
            fixtures = r2.json().get("events", [])
            st.write(f"Partidos próximos encontrados: {len(fixtures)}")

            if not fixtures:
                st.warning("No hay partidos próximos para esta liga.")
            else:
                for f in fixtures:
                    fecha = f.get("dateEvent")
                    hora = f.get("strTime")
                    home = f.get("strHomeTeam")
                    away = f.get("strAwayTeam")
                    status = f.get("strStatus") or "Programado"
                    st.write(f"{fecha} {hora} — {home} vs {away} | Estado: {status}")
