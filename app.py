import streamlit as st
import pandas as pd
import requests
import html
from datetime import datetime, timedelta

# ────────────────────────────────────────────────
# CONFIG (SIEMPRE PRIMERO)
# ────────────────────────────────────────────────
st.set_page_config(page_title="InsideBet - Futbol Picks", layout="wide")

# 🔐 API desde secrets
API_KEY = st.secrets["API_KEY"]
BASE_URL = "https://api.football-data.org/v4"
headers = {"X-Auth-Token": API_KEY}

LIGAS = {
    "CL": "UEFA Champions League",
    "PL": "Premier League",
}

dias_futuros = 2


# ────────────────────────────────────────────────
# CSS MODERNO CON SCROLL VERTICAL
# ────────────────────────────────────────────────
st.markdown("""
<style>

.table-container {
    overflow-x: auto;
    overflow-y: auto;
    max-height: 500px;
    margin-top: 15px;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
}

.custom-table {
    border-collapse: collapse;
    width: 100%;
    font-size: 15px;
}

.custom-table th {
    background-color: #111827;
    color: white;
    padding: 12px;
    text-align: center;
    position: sticky;
    top: 0;
    z-index: 2;
}

.custom-table td {
    padding: 10px;
    text-align: center;
    border-bottom: 1px solid #e5e7eb;
}

.custom-table tr:hover {
    background-color: #f3f4f6;
}

.badge-green {
    background-color: #16a34a;
    color: white;
    padding: 5px 10px;
    border-radius: 10px;
    font-weight: bold;
}

.badge-red {
    background-color: #dc2626;
    color: white;
    padding: 5px 10px;
    border-radius: 10px;
    font-weight: bold;
}

.badge-yellow {
    background-color: #eab308;
    color: black;
    padding: 5px 10px;
    border-radius: 10px;
    font-weight: bold;
}

.score-high {
    color: #16a34a;
    font-weight: bold;
}

.score-mid {
    color: #eab308;
    font-weight: bold;
}

.score-low {
    color: #dc2626;
    font-weight: bold;
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
            return [], f"Error {r.status_code}: {r.text}"

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
            sh = m["score"]["fullTime"]["home"] or 0
            sa = m["score"]["fullTime"]["away"] or 0

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
# PROCESAR PARTIDOS
# ────────────────────────────────────────────────
def procesar_partidos(matches):

    datos = []
    vistos = set()
    stats_cache = {}

    for p in matches:

        home_name = p["homeTeam"]["shortName"] or p["homeTeam"]["name"]
        away_name = p["awayTeam"]["shortName"] or p["awayTeam"]["name"]

        fecha = p["utcDate"][:10]
        hora = p["utcDate"][11:16]

        partido_key = f"{home_name}-{away_name}-{fecha}-{hora}"

        if partido_key in vistos:
            continue
        vistos.add(partido_key)

        home_id = p["homeTeam"]["id"]
        away_id = p["awayTeam"]["id"]

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
            "Top Pick": top_pick + (" 🔥" if score > 6 else ""),
            "Score": round(score, 1)
        })

    return pd.DataFrame(datos).sort_values("Hora")


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

            table_html = "<div class='table-container'><table class='custom-table'>"
            table_html += "<tr><th>Fecha</th><th>Hora</th><th>Partido</th><th>BTTS</th><th>O/U 2.5</th><th>Top Pick</th><th>Score</th></tr>"

            for _, row in df.iterrows():

                if row["Score"] >= 6:
                    score_class = "score-high"
                elif row["Score"] >= 4:
                    score_class = "score-mid"
                else:
                    score_class = "score-low"

                if "Over" in row["Top Pick"] or "Yes" in row["Top Pick"]:
                    badge_class = "badge-green"
                elif "Under" in row["Top Pick"] or "No" in row["Top Pick"]:
                    badge_class = "badge-red"
                else:
                    badge_class = "badge-yellow"

                table_html += f"""
                <tr>
                    <td>{html.escape(str(row['Fecha']))}</td>
                    <td>{html.escape(str(row['Hora']))}</td>
                    <td><strong>{html.escape(str(row['Partido']))}</strong></td>
                    <td>{html.escape(str(row['BTTS']))}</td>
                    <td>{html.escape(str(row['O/U 2.5']))}</td>
                    <td><span class="{badge_class}">{row['Top Pick']}</span></td>
                    <td class="{score_class}">{row['Score']}</td>
                </tr>
                """

            table_html += "</table></div>"

            st.markdown(html, unsafe_allow_html=True)
            st.success(f"{len(df)} partidos encontrados.")

        else:
            st.warning("No hay partidos programados en el rango seleccionado.")
