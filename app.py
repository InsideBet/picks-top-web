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

# API Football
API_KEY_AF = st.secrets["API_KEY_AF"]  # Tu key de API-Football
BASE_URL_AF = "https://v3.football.api-sports.io"
HEADERS_AF = {"x-apisports-key": API_KEY_AF}

# Ligas y banderas
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

LIGAS_AF_ID = {
    "CL": 2,
    "PL": 39,
    "PD": 140,
    "SA": 135,
    "FL1": 61,
    "BL1": 78,
    "PPL": 94,
    "DED": 88,
}

BANDERAS = {
    "PL": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/be/Flag_of_England.svg/250px-Flag_of_England.svg.png",
    "PD": "https://upload.wikimedia.org/wikipedia/en/thumb/9/9a/Flag_of_Spain.svg/960px-Flag_of_Spain.svg.png",
    "SA": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/03/Flag_of_Italy.svg/250px-Flag_of_Italy.svg.png",
    "FL1": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Flag_of_France.svg/1280px-Flag_of_France.svg.png",
    "BL1": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Flag_of_Germany.svg/1280px-Flag_of_Germany.svg.png",
    "PPL": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Flag_of_Portugal_%28official%29.svg/1280px-Flag_of_Portugal_%28official%29.svg.png",
    "DED": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Flag_of_the_Netherlands.svg/1280px-Flag_of_the_Netherlands.svg.png",
    "CL": "https://i.postimg.cc/28pJqYLN/UEFA-Champions-League-logo.png"
}

DIAS_FUTUROS = 2
THESPORTSDB_KEY = "123"  # Key pública TheSportsDB

# ────────────────────────────────────────────────
# ESTILO STREAMLIT
# ────────────────────────────────────────────────
st.markdown("""
<style>
.stApp {
    background-color: #0e1117;
    color: #e5e7eb;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center; margin-top:15px; margin-bottom:20px;">
    <img src="https://i.postimg.cc/hPkSPNcT/Sin-titulo-2.png" width="280"><br>
    <p style="
        font-family: 'Montserrat', sans-serif;
        font-size:18px;
        font-weight:500;
        color:#e5e7eb;
        margin-top:10px;
    ">
       Partidos & Estadísticas
    </p>
</div>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# FUNCIONES API
# ────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def cargar_fixtures_af(league_id):
    """Trae fixtures próximos de API-Football"""
    from_date = datetime.now().strftime("%Y-%m-%d")
    to_date = (datetime.now() + timedelta(days=DIAS_FUTUROS)).strftime("%Y-%m-%d")
    url = f"{BASE_URL_AF}/fixtures"
    params = {
        "league": league_id,
        "season": 2025,
        "from": from_date,
        "to": to_date
    }
    r = requests.get(url, headers=HEADERS_AF, params=params, timeout=10)
    if r.status_code != 200:
        return [], f"Error {r.status_code}"
    return r.json().get("response", []), None

@st.cache_data(ttl=3600)
def get_odds_af(fixture_id):
    """Obtiene odds 1X2, Over/Under 2.5 y BTTS"""
    url = f"{BASE_URL_AF}/odds"
    params = {"fixture": fixture_id, "bookmaker": 6}
    r = requests.get(url, headers=HEADERS_AF, params=params, timeout=10)
    if r.status_code != 200:
        return {}
    data = r.json().get("response", [])
    if not data:
        return {}
    markets = data[0].get("bookmakers", [{}])[0].get("bets", [])
    odds_dict = {}
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
    return odds_dict

@st.cache_data(ttl=3600)
def get_statistics_af(fixture_id):
    """Obtiene corners y tarjetas"""
    url = f"{BASE_URL_AF}/fixtures/statistics"
    params = {"fixture": fixture_id}
    r = requests.get(url, headers=HEADERS_AF, params=params, timeout=10)
    if r.status_code != 200:
        return {}
    stats = r.json().get("response", [])
    if not stats:
        return {}
    result = {}
    for s in stats:
        team = s.get("team", {}).get("name")
        for st in s.get("statistics", []):
            if st.get("type") == "Corner":
                result[f"Corners {team}"] = st.get("value")
            if st.get("type") == "Yellow Card":
                result[f"Yellow {team}"] = st.get("value")
            if st.get("type") == "Red Card":
                result[f"Red {team}"] = st.get("value")
    return result

# ────────────────────────────────────────────────
# TheSportsDB funciones
# ────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def cargar_fixtures_tsdb(liga_nombre):
    """Trae fixtures próximos de TheSportsDB"""
    url_teams = f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_KEY}/search_all_teams.php"
    params = {"l": liga_nombre}
    r = requests.get(url_teams, params=params, timeout=10)
    if r.status_code != 200:
        return [], f"Error TSDB {r.status_code}"
    teams = r.json().get("teams")
    if not teams:
        return [], "No se encontraron equipos en TSDB"
    fixtures = []
    for team in teams:
        team_id = team.get("idTeam")
        if not team_id:
            continue
        url_events = f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_KEY}/eventsnext.php"
        r2 = requests.get(url_events, params={"id": team_id}, timeout=10)
        if r2.status_code != 200:
            continue
        events = r2.json().get("events")
        if events:
            fixtures.extend(events)
    return fixtures, None

def procesar_fixtures_af(fixtures):
    """Convierte fixtures API-Football a DataFrame"""
    datos = []
    for f in fixtures:
        fixture_id = f["fixture"]["id"]
        home = f["teams"]["home"]
        away = f["teams"]["away"]
        fecha = f["fixture"]["date"][:10]
        hora = f["fixture"]["date"][11:16]
        partido = f"{home['name']} vs {away['name']}"
        odds = get_odds_af(fixture_id)
        odds_1X2 = odds.get("1X2", {})
        odds_OU = odds.get("O/U 2.5", {})
        odds_BTTS = odds.get("BTTS", {})
        stats = get_statistics_af(fixture_id)
        corners_home = stats.get(f"Corners {home['name']}", "N/A")
        corners_away = stats.get(f"Corners {away['name']}", "N/A")
        yellow_home = stats.get(f"Yellow {home['name']}", "N/A")
        yellow_away = stats.get(f"Yellow {away['name']}", "N/A")
        red_home = stats.get(f"Red {home['name']}", "N/A")
        red_away = stats.get(f"Red {away['name']}", "N/A")
        pct_btts = 50
        avg_goles = 2
        score = round(avg_goles * (pct_btts/100) * 2.5,1)
        pick_btts = "Yes" if pct_btts > 65 else "No"
        pick_over = "Over 2.5" if avg_goles > 2.5 else "Under 2.5"
        top_pick = pick_btts if pct_btts > 70 else pick_over
        datos.append({
            "Fecha 📅": fecha,
            "Hora ⏱️": hora,
            "Partido 🆚": partido,
            "1X2 Odds": odds_1X2 or "N/A",
            "O/U 2.5 Odds": odds_OU or "N/A",
            "BTTS Odds": odds_BTTS or "N/A",
            "Corners Home": corners_home,
            "Corners Away": corners_away,
            "Yellow Home": yellow_home,
            "Yellow Away": yellow_away,
            "Red Home": red_home,
            "Red Away": red_away,
            "BTTS ⚽": pick_btts,
            "O/U 2.5 ⚽": pick_over,
            "Top Pick 🔥": top_pick,
            "Score": score
        })
    return pd.DataFrame(datos)

def procesar_fixtures_tsdb(fixtures):
    """Convierte fixtures TSDB a DataFrame"""
    datos = []
    for f in fixtures:
        home = f.get("strHomeTeam")
        away = f.get("strAwayTeam")
        fecha = f.get("dateEvent") or "N/A"
        hora = f.get("strTime") or "N/A"
        pct_btts = 50
        avg_goles = 2
        score = round(avg_goles * (pct_btts/100) * 2.5,1)
        pick_btts = "Yes" if pct_btts > 65 else "No"
        pick_over = "Over 2.5" if avg_goles > 2.5 else "Under 2.5"
        top_pick = pick_btts if pct_btts > 70 else pick_over
        datos.append({
            "Fecha 📅": fecha,
            "Hora ⏱️": hora,
            "Partido 🆚": f"{home} vs {away}",
            "1X2 Odds": "N/A",
            "O/U 2.5 Odds": "N/A",
            "BTTS Odds": "N/A",
            "Corners Home": "N/A",
            "Corners Away": "N/A",
            "Yellow Home": "N/A",
            "Yellow Away": "N/A",
            "Red Home": "N/A",
            "Red Away": "N/A",
            "BTTS ⚽": pick_btts,
            "O/U 2.5 ⚽": pick_over,
            "Top Pick 🔥": top_pick,
            "Score": score
        })
    return pd.DataFrame(datos)

# ────────────────────────────────────────────────
# INTERFAZ STREAMLIT SEGURA
# ────────────────────────────────────────────────
tabs = st.tabs(list(LIGAS.values()))

for tab, (code, nombre) in zip(tabs, LIGAS.items()):
    with tab:
        st.markdown(f"### {nombre}")
        st.image(BANDERAS[code], width=60)

        # Traer fixtures API-Football
        fixtures_af, error_af = cargar_fixtures_af(LIGAS_AF_ID[code])
        if error_af:
            st.error(f"API-Football: {error_af}")

        df_af = procesar_fixtures(fixtures_af) if fixtures_af else pd.DataFrame()

        # Aquí podrías agregar TheSportsDB si querés combinar
        # Ejemplo (opcional):
        # fixtures_tsdb, error_tsdb = cargar_fixtures_tsdb(LIGAS_TSDB[code])
        # df_tsdb = procesar_tsdb(fixtures_tsdb) if fixtures_tsdb else pd.DataFrame()

        # Para probar solo API-Football:
        df_tsdb = pd.DataFrame()  

        # Concatenar de manera segura
        if df_af.empty and df_tsdb.empty:
            df = pd.DataFrame(columns=[
                "Fecha 📅","Hora ⏱️","Partido 🆚","1X2 Odds","O/U 2.5 Odds","BTTS Odds",
                "Corners Home","Corners Away","Yellow Home","Yellow Away",
                "Red Home","Red Away","BTTS ⚽","O/U 2.5 ⚽","Top Pick 🔥","Score"
            ])
        else:
            df = pd.concat([df_af, df_tsdb], ignore_index=True)
            df.drop_duplicates(subset=["Fecha 📅","Partido 🆚"], inplace=True)

        # Asegurarnos de que Score exista
        if "Score" not in df.columns:
            df["Score"] = 0

        # Ordenar por Score
        df = df.sort_values("Score", ascending=False)

        if df.empty:
            st.warning("No hay partidos programados en el rango seleccionado.")
        else:
            st.dataframe(
                df,
                use_container_width=True,
                height=600,
                hide_index=True,
                column_config={
                    "Score": st.column_config.ProgressColumn(
                        "Score",
                        help="Nivel de confianza del pick",
                        min_value=0,
                        max_value=10,
                        format="%.1f"
                    ),
                }
            )
            st.success(f"{len(df)} partidos encontrados.")

