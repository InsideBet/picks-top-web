import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# ────────────────────────────────────────────────
# CONFIGURACIÓN (pegá tu key aquí)
# ────────────────────────────────────────────────
API_KEY = "19f74cf44a5449c29d2b3000848bdfa8"  # ← Cambiá esto por tu key real
BASE_URL = "https://api.football-data.org/v4"
headers = {"X-Auth-Token": API_KEY}

LIGAS = {
    "PL": "Premier League",
    "CL": "UEFA Champions League",
}

dias_futuros = 2

# ────────────────────────────────────────────────
# FUNCIONES DEL BOT
# ────────────────────────────────────────────────

def get_partidos_futuros_liga(competition_code):
    today = datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=dias_futuros)).strftime('%Y-%m-%d')
    url = f"{BASE_URL}/competitions/{competition_code}/matches"
    params = {"dateFrom": today, "dateTo": end_date, "status": "SCHEDULED"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code != 200:
            st.error(f"Error en API para {competition_code}: {r.status_code}")
            return []
        return r.json().get('matches', [])
    except Exception as e:
        st.error(f"Excepción: {e}")
        return []

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
# INTERFAZ DE STREAMLIT
# ────────────────────────────────────────────────

st.set_page_config(page_title="Futbol Picks - InsideBet", layout="wide")

st.title("⚽ Futbol Picks - Próximos Partidos")
st.markdown("Datos reales de football-data.org | Actualizado automáticamente")

# Cargar datos
with st.spinner("Cargando partidos futuros..."):
    todos_datos = []
    for code, liga in LIGAS.items():
        partidos = get_partidos_futuros_liga(code)
        for p in partidos:
            home_id = p['homeTeam']['id']
            away_id = p['awayTeam']['id']
            home_name = p['homeTeam']['shortName'] or p['homeTeam']['name']
            away_name = p['awayTeam']['shortName'] or p['awayTeam']['name']

            stats_home = get_stats_historicos(home_id)
            stats_away = get_stats_historicos(away_id)

            avg_goles = (stats_home['avg_goles'] + stats_away['avg_goles']) / 2
            pct_btts = (stats_home['pct_btts'] + stats_away['pct_btts']) / 2
            score = avg_goles * (pct_btts / 100) * 2.5

            pick_btts = "Yes" if pct_btts > 65 else "No"
            pick_over = "Over 2.5" if avg_goles > 2.5 else "Under 2.5"
            top_pick = pick_btts if pct_btts > 70 else pick_over

            todos_datos.append({
                "Liga": liga,
                "Hora": p['utcDate'][11:16],
                "Partido": f"{home_name} vs {away_name}",
                "BTTS": f"{pick_btts} ({round(pct_btts)}%)",
                "O/U 2.5": pick_over,
                "Top Pick": top_pick + (" 🔥" if score > 6 else ""),
                "Score": round(score, 1)
            })

    if todos_datos:
        df = pd.DataFrame(todos_datos)
        df = df.sort_values("Hora")  # Ordenar por hora

        st.dataframe(
            df.style.set_properties(**{'text-align': 'center'})
                    .highlight_max(subset=['Score'], color='#d4edda')
                    .format(precision=1),
            use_container_width=True,
            hide_index=True
        )

        st.success(f"Se encontraron {len(df)} partidos en las próximas {dias_futuros*24} horas.")
    else:
        st.warning("No hay partidos programados en las próximas 48 horas. Probá ampliando el rango o chequeando ligas.")
