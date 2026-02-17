import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# ────────────────────────────────────────────────
# CONFIGURACIÓN
# ────────────────────────────────────────────────
API_KEY = "19f74cf44a5449c29d2b3000848bdfa8"  # Pegá tu key real
BASE_URL = "https://api.football-data.org/v4"
headers = {"X-Auth-Token": API_KEY}

# Ligas con sus códigos y nombres amigables
LIGAS = {
    "PL": "Premier League",
    "CL": "UEFA Champions League",
    "PD": "La Liga",
    "BL1": "Bundesliga",
    "SA": "Serie A",
    # Agregá más cuando quieras: "FL1": "Ligue 1", etc.
}

dias_futuros = 7  # Próxima semana para traer más datos

@st.cache_data(ttl=1800)  # Cache 30 min para evitar rate limit
def cargar_partidos_liga(code):
    today = datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=dias_futuros)).strftime('%Y-%m-%d')
    url = f"{BASE_URL}/competitions/{code}/matches"
    params = {"dateFrom": today, "dateTo": end_date, "status": "SCHEDULED"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code != 200:
            return pd.DataFrame(), f"Error en API ({r.status_code})"
        matches = r.json().get('matches', [])
        return matches, None
    except Exception as e:
        return pd.DataFrame(), str(e)

def procesar_partidos(matches, liga_nombre):
    datos = []
    for p in matches:
        home_id = p['homeTeam']['id']
        away_id = p['awayTeam']['id']
        home_name = p['homeTeam']['shortName'] or p['homeTeam']['name']
        away_name = p['awayTeam']['shortName'] or p['awayTeam']['name']

        # Stats históricos (simplificado)
        stats_home = get_stats_historicos(home_id)
        stats_away = get_stats_historicos(away_id)

        avg_goles = (stats_home['avg_goles'] + stats_away['avg_goles']) / 2
        pct_btts = (stats_home['pct_btts'] + stats_away['pct_btts']) / 2
        score = avg_goles * (pct_btts / 100) * 2.5

        pick_btts = "Yes" if pct_btts > 65 else "No"
        pick_over = "Over 2.5" if avg_goles > 2.5 else "Under 2.5"
        top_pick = pick_btts if pct_btts > 70 else pick_over

        datos.append({
            "Hora": p['utcDate'][11:16],
            "Partido": f"{home_name} vs {away_name}",
            "BTTS": f"{pick_btts} ({round(pct_btts)}%)",
            "O/U 2.5": pick_over,
            "Top Pick": top_pick + (" 🔥" if score > 6 else ""),
            "Score": round(score, 1)
        })
    df = pd.DataFrame(datos)
    return df.sort_values("Hora") if not df.empty else pd.DataFrame()

def get_stats_historicos(equipo_id, limite=5):
    url = f"{BASE_URL}/teams/{equipo_id}/matches"
    params = {"status": "FINISHED", "limit": limite}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code != 200: return {"avg_goles": 0, "pct_btts": 0}
        matches = r.json().get('matches', [])
        if not matches: return {"avg_goles": 0, "pct_btts": 0}

        total_goles = 0
        btts_count = 0
        for m in matches:
            sh = m['score']['fullTime']['home'] or 0
            sa = m['score']['fullTime']['away'] or 0
            total = sh + sa
            total_goles += total
            if sh > 0 and sa > 0: btts_count += 1

        n = len(matches)
        return {
            "avg_goles": total_goles / n if n else 0,
            "pct_btts": (btts_count / n) * 100 if n else 0
        }
    except:
        return {"avg_goles": 0, "pct_btts": 0}

# ────────────────────────────────────────────────
# INTERFAZ
# ────────────────────────────────────────────────

st.set_page_config(page_title="InsideBet - Futbol Picks", layout="wide")

st.title("⚽ InsideBet - Próximos Partidos")
st.markdown("Selecciona una liga para ver los partidos y picks")

# Botones para cada liga
cols = st.columns(min(3, len(LIGAS)))  # Columnas para botones (máx 3 por fila)
for i, (code, nombre) in enumerate(LIGAS.items()):
    with cols[i % len(cols)]:
        if st.button(nombre, key=f"btn_{code}", use_container_width=True):
            with st.spinner(f"Cargando partidos de {nombre}..."):
                matches, error = cargar_partidos_liga(code)
                if error:
                    st.error(error)
                elif matches:
                    df = procesar_partidos(matches, nombre)
                    st.subheader(f"Partidos en {nombre}")
                    st.dataframe(
                        df.style.set_properties(**{'text-align': 'center'})
                                .highlight_max(subset=['Score'], color='#d4edda')
                                .format(precision=1),
                        use_container_width=True,
                        hide_index=True
                    )
                    st.success(f"Encontrados {len(df)} partidos.")
                else:
                    st.warning("No hay partidos programados en el rango para esta liga.")
