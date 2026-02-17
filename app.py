import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# ────────────────────────────────────────────────
# CONFIGURACIÓN
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="InsideBet - Futbol Picks",
    layout="wide"
)

API_KEY = st.secrets["API_KEY"]
BASE_URL = "https://api.football-data.org/v4"
headers = {"X-Auth-Token": API_KEY}

LIGAS = {
    "CL": "UEFA Champions League",
    "PL": "Premier League",
}

dias_futuros = 2

# Tema dark general
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
        "status": "SCHEDULED"
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

        if home_id not in stats_cache:
            stats_cache[home_id] = get_stats_historicos(home_id)

        if away_id not in stats_cache:
            stats_cache[away_id] = get_stats_historicos(away_id)

        stats_home = stats_cache[home_id]
        stats_away = stats_cache[away_id]

        avg_goles = (stats_home["avg_goles"] + stats_away["avg_goles"]) / 2
        pct_btts = (stats_home["pct_btts"] + stats_away["pct_btts"]) / 2

        score = avg_goles * (pct_btts / 100) * 2.5

        pick_btts = "Yes" if pct_btts > 65 else "No"
        pick_over = "Over 2.5" if avg_goles > 2.5 else "Under 2.5"
        top_pick = pick_btts if pct_btts > 70 else pick_over

        datos.append({
            "Fecha": fecha,
            "Hora": hora,
            "Partido": f"{home_name} vs {away_name}",
            "BTTS": f"{pick_btts} ({round(pct_btts)}%)",
            "O/U 2.5": pick_over,
            "Top Pick": top_pick,
            "Score": round(score, 1)
        })

    return pd.DataFrame(datos)


# ────────────────────────────────────────────────
# INTERFAZ
# ────────────────────────────────────────────────
st.title("⚽ InsideBet")
st.markdown("### Próximos Partidos & Picks Automáticos")

for code, nombre in LIGAS.items():

    if f"show_{code}" not in st.session_state:
        st.session_state[f"show_{code}"] = False

    if st.button(nombre, key=f"btn_{code}", use_container_width=True):
        st.session_state[f"show_{code}"] = not st.session_state[f"show_{code}"]

    if st.session_state[f"show_{code}"]:

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
                    height=500,
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


