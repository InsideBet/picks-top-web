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

API_KEY = st.secrets["API_KEY"]
BASE_URL = "https://api.football-data.org/v4"
headers = {"X-Auth-Token": API_KEY}

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
    # Logo oficial de la Premier League
    "PL": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Flag_of_the_United_Kingdom_%281-2%29.svg/1920px-Flag_of_the_United_Kingdom_%281-2%29.svg.png",  # :contentReference[oaicite:1]{index=1}

    # La Liga (España) — último logo vertical disponible
    "PD": "https://upload.wikimedia.org/wikipedia/en/thumb/9/9a/Flag_of_Spain.svg/960px-Flag_of_Spain.svg.png?20160610210450",  # :contentReference[oaicite:2]{index=2}

    # Serie A Italia logo oficial
    "SA": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/03/Flag_of_Italy.svg/250px-Flag_of_Italy.svg.png",  # :contentReference[oaicite:3]{index=3}

    # Ligue 1 logo oficial
    "FL1": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Flag_of_France.svg/1280px-Flag_of_France.svg.png",  # :contentReference[oaicite:4]{index=4}

    # Bundesliga logo oficial
    "BL1": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Flag_of_Germany.svg/1280px-Flag_of_Germany.svg.png",  # :contentReference[oaicite:5]{index=5}

    # Primeira Liga (Portugal) — puede ser Liga NOS logo (similar)
    "PPL": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Flag_of_Portugal_%28official%29.svg/1280px-Flag_of_Portugal_%28official%29.svg.png",  # :contentReference[oaicite:6]{index=6}

    # Eredivisie (Países Bajos) logo oficial
    "DED": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Flag_of_the_Netherlands.svg/1280px-Flag_of_the_Netherlands.svg.png",  # :contentReference[oaicite:7]{index=7}

    # Champions League — logo UEFA
    "CL": "https://i.postimg.cc/28pJqYLN/UEFA-Champions-League-logo.png"
}

dias_futuros = 2

#Tema dark general
st.markdown("""
<style>
.stApp {
    background-color: #0f172a;
    color: #e5e7eb;
}
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# API CALLS
# ────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def cargar_partidos_liga(code):
    today = datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=dias_futuros)).strftime('%Y-%m-%d')

    url = f"{BASE_URL}/competitions/{code}/matches"
    params = {
        "dateFrom": today,
        "dateTo": end_date,
    }

    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)

        if r.status_code == 429:
            return [], "Rate limit alcanzado. Esperá 60 segundos."

        if r.status_code != 200:
            return [], f"Error {r.status_code}"

        return r.json().get("matches", []), None

    except Exception as e:
        return [], f"Error conexión: {str(e)}"


@st.cache_data(ttl=3600)
def get_stats_historicos(equipo_id, limite=5):
    url = f"{BASE_URL}/teams/{equipo_id}/matches"
    params = {"status": "FINISHED", "limit": limite}

    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)

        if r.status_code != 200:
            return {"avg_goles": 0, "pct_btts": 0}

        matches = r.json().get("matches", [])
        if not matches:
            return {"avg_goles": 0, "pct_btts": 0}

        total_goles = 0
        btts_count = 0

        for m in matches:
            full_time = m.get("score", {}).get("fullTime", {})
            sh = full_time.get("home") or 0
            sa = full_time.get("away") or 0

            total_goles += sh + sa
            if sh > 0 and sa > 0:
                btts_count += 1

        n = len(matches)

        return {
            "avg_goles": total_goles / n if n else 0,
            "pct_btts": (btts_count / n) * 100 if n else 0
        }

    except Exception:
        return {"avg_goles": 0, "pct_btts": 0}


# ────────────────────────────────────────────────
# PROCESAMIENTO
# ────────────────────────────────────────────────
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

        # Obtener estadísticas históricas
        if home_id not in stats_cache:
            stats_cache[home_id] = get_stats_historicos(home_id)
        if away_id not in stats_cache:
            stats_cache[away_id] = get_stats_historicos(away_id)

        stats_home = stats_cache[home_id]
        stats_away = stats_cache[away_id]

        avg_goles = (stats_home["avg_goles"] + stats_away["avg_goles"]) / 2
        pct_btts = (stats_home["pct_btts"] + stats_away["pct_btts"]) / 2

        # Nivel de confianza
        score = round(avg_goles * (pct_btts / 100) * 2.5, 1)

        # Picks
        pick_btts = "Yes" if pct_btts > 65 else "No"
        pick_over = "Over 2.5" if avg_goles > 2.5 else "Under 2.5"
        top_pick = pick_btts if pct_btts > 70 else pick_over

        datos.append({
            "Fecha 📅": fecha,
            "Hora ⏱️": hora,
            "Partido 🆚": f"{home_name} vs {away_name}",
            "BTTS ⚽": f"{pick_btts} ({round(pct_btts)}%)",
            "O/U 2.5 ⚽": pick_over,
            "Top Pick 🔥": top_pick,
            "Score": score
        })

    return pd.DataFrame(datos)

# ────────────────────────────────────────────────
# INTERFAZ
# ────────────────────────────────────────────────
st.image("https://i.postimg.cc/bJcbxmxg/insidebet.png", width=250)
st.markdown("### Próximos Partidos & Estadísticas", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

tabs = st.tabs(list(LIGAS.values()))

for tab, (code, nombre) in zip(tabs, LIGAS.items()):
    with tab:
        st.markdown(f"### {nombre}")  # nombre de la liga
        st.image(BANDERAS[code], width=60) # bandera/logo al lado
        matches, error = cargar_partidos_liga(code)
        # tu código existente para procesar y mostrar los partidos

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

