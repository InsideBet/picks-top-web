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
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

LIGAS = {
    "CL": "Champions League",
    "EL": "Europa League",
    "PL": "Premier League",
    "PD": "La Liga",
    "SA": "Serie A",
    "FL1": "Ligue 1",
    "BL1": "Bundesliga",
    "ASL": "Liga Argentina",
}

dias_futuros = 2

# Tema dark
st.markdown("""
<style>
.stApp {
    background-color: #0f172a;
    color: #e5e7eb;
}
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# FUNCIONES API
# ────────────────────────────────────────────────
@st.cache_data(ttl=300)
def cargar_partidos_liga(league_code):
    today = datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=dias_futuros)).strftime('%Y-%m-%d')

    url = f"{BASE_URL}/fixtures"
    params = {
        "league": league_code,
        "season": datetime.now().year,
        "from": today,
        "to": end_date,
        "status": "NS,TBD,1H,2H,FT"  # Incluir todos los próximos y en vivo
    }

    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        data = r.json().get("response", [])
        return data, None
    except Exception as e:
        return [], f"Error conexión: {e}"

@st.cache_data(ttl=3600)
def get_stats_team(team_id, league_id):
    """Obtiene estadísticas recientes reales de un equipo."""
    url = f"{BASE_URL}/teams/statistics"
    params = {"team": team_id, "league": league_id, "season": datetime.now().year}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        data = r.json().get("response", {})

        played_home = max(1, data['fixtures']['played']['total']['home'])
        played_away = max(1, data['fixtures']['played']['total']['away'])
        total_played = played_home + played_away

        # Goles promedio
        goals_for = data['fixtures']['goals']['for']['total']['home'] + data['fixtures']['goals']['for']['total']['away']
        goals_against = data['fixtures']['goals']['against']['total']['home'] + data['fixtures']['goals']['against']['total']['away']
        avg_goals = (goals_for + goals_against) / total_played

        # BTTS %
        pct_btts = data.get("fixtures", {}).get("goals", {}).get("bothTeamsToScore", {}).get("total", 0)

        # Corners promedio
        corners_total = data.get("fixtures", {}).get("corners", {}).get("total", {}).get("home", 0) + \
                        data.get("fixtures", {}).get("corners", {}).get("total", {}).get("away", 0)
        avg_corners = corners_total / total_played

        # Tarjetas promedio
        cards_total = data.get("fixtures", {}).get("cards", {}).get("total", {}).get("home", 0) + \
                      data.get("fixtures", {}).get("cards", {}).get("total", {}).get("away", 0)
        avg_cards = cards_total / total_played

        return {"avg_goals": avg_goals, "pct_btts": pct_btts,
                "corners_avg": avg_corners, "cards_avg": avg_cards}

    except Exception as e:
        print("Error stats team:", e)
        return {"avg_goals": 0, "pct_btts": 0, "corners_avg": 0, "cards_avg": 0}

# ────────────────────────────────────────────────
# PROCESAMIENTO
# ────────────────────────────────────────────────
def procesar_partidos(matches, league_id):
    datos = []
    stats_cache = {}

    def format_pm(value, threshold):
        if round(value) == 0:
            return "0"
        return f"+{round(value)}" if value >= threshold else f"-{round(value)}"

    threshold_corners = 10
    threshold_cards = 3

    for p in matches:
        fixture = p['fixture']
        home = p['teams']['home']
        away = p['teams']['away']
        home_id = home['id']
        away_id = away['id']
        home_name = home['name']
        away_name = away['name']

        fecha = fixture['date'][:10]
        hora = fixture['date'][11:16]

        # Estado del partido
        estado_short = fixture['status']['short']
        if estado_short in ["NS", "TBD"]:
            estado_display = "Por empezar"
        elif estado_short in ["1H", "2H"]:
            estado_display = "En Vivo"
        elif estado_short == "FT":
            estado_display = "Finalizado"
        else:
            estado_display = estado_short

        # Stats home
        if home_id not in stats_cache:
            stats_cache[home_id] = get_stats_team(home_id, league_id)
        if away_id not in stats_cache:
            stats_cache[away_id] = get_stats_team(away_id, league_id)

        sh = stats_cache[home_id]
        sa = stats_cache[away_id]

        # Promedios combinados
        avg_goles = (sh['avg_goals'] + sa['avg_goals']) / 2
        pct_btts = (sh['pct_btts'] + sa['pct_btts']) / 2
        confidence = round(avg_goles * (pct_btts / 100) * 2.5, 1)

        # Picks
        pick_btts = "Yes" if pct_btts > 65 else "No"
        pick_over = "Over 2.5" if avg_goles > 2.5 else "Under 2.5"
        top_pick = pick_btts if pct_btts > 70 else pick_over

        # Corners y tarjetas
        avg_corners = (sh['corners_avg'] + sa['corners_avg']) / 2
        avg_cards = (sh['cards_avg'] + sa['cards_avg']) / 2
        corners_display = format_pm(avg_corners, threshold_corners)
        cards_display = format_pm(avg_cards, threshold_cards)

        datos.append({
            "Fecha 📅": fecha,
            "Hora ⏱️": hora,
            "Partido 🆚": f"{home_name} vs {away_name}",
            "Estado 🕒": estado_display,
            "BTTS ⚽": f"{pick_btts} ({round(pct_btts)}%)",
            "O/U 2.5 ⚽": pick_over,
            "Top Pick 🔥": top_pick,
            "Score": confidence,
            "Corners 🚩": corners_display,
            "Tarjetas 🟨🟥": cards_display
        })

    return pd.DataFrame(datos)

# ────────────────────────────────────────────────
# INTERFAZ
# ────────────────────────────────────────────────
st.title("⚽ InsideBet")
st.markdown("### Próximos Partidos & Estadísticas")

tabs = st.tabs(list(LIGAS.values()))

for tab, (league_code, league_name) in zip(tabs, LIGAS.items()):
    with tab:
        matches, error = cargar_partidos_liga(league_code)
        if error:
            st.error(error)
        elif matches:
            df = procesar_partidos(matches, league_code)
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
