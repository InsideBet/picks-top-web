import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

API_KEY = "19f74cf44a5449c29d2b3000848bdfa8"
BASE_URL = "https://api.football-data.org/v4"
headers = {"X-Auth-Token": API_KEY}

LIGAS = {
    "CL": "UEFA Champions League",  # Solo esta por ahora para evitar 429
    # "PL": "Premier League",  # Descomenta cuando pase el límite
}

dias_futuros = 7

@st.cache_data(ttl=3600)  # Cache 1 hora
def cargar_partidos_liga(code):
    today = datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=dias_futuros)).strftime('%Y-%m-%d')
    url = f"{BASE_URL}/competitions/{code}/matches"
    params = {"dateFrom": today, "dateTo": end_date, "status": "SCHEDULED"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code == 429:
            return [], "Rate limit (esperá 60 segundos)"
        if r.status_code != 200:
            return [], f"Error {r.status_code}: {r.text}"
        return r.json().get('matches', []), None
    except Exception as e:
        return [], str(e)

def procesar_partidos(matches, liga_nombre):
    datos = []
    vistos = set()  # Set para claves únicas

    for p in matches:
        home_name = p['homeTeam']['shortName'] or p['homeTeam']['name']
        away_name = p['awayTeam']['shortName'] or p['awayTeam']['name']
        hora = p['utcDate'][11:16]
        fecha = p['utcDate'][:10]

        # Clave única: equipos + fecha + hora (evita duplicados)
        partido_key = f"{home_name}-{away_name}-{fecha}-{hora}"

        if partido_key in vistos:
            continue  # Salta si ya lo procesamos
        vistos.add(partido_key)

        home_id = p['homeTeam']['id']
        away_id = p['awayTeam']['id']

        stats_home = get_stats_historicos(home_id)
        stats_away = get_stats_historicos(away_id)

        avg_goles = (stats_home['avg_goles'] + stats_away['avg_goles']) / 2
        pct_btts = (stats_home['pct_btts'] + stats_away['pct_btts']) / 2
        score = avg_goles * (pct_btts / 100) * 2.5

        pick_btts = "Yes" if pct_btts > 65 else "No"
        pick_over = "Over 2.5" if avg_goles > 2.5 else "Under 2.5"
        top_pick = pick_btts if pct_btts > 70 else pick_over

        datos.append({
            "Liga": liga_nombre,
            "Hora": hora,
            "Partido": f"{home_name} vs {away_name}",
            "BTTS": f"{pick_btts} ({round(pct_btts)}%)",
            "O/U 2.5": pick_over,
            "Top Pick": top_pick + (" 🔥" if score > 6 else ""),
            "Score": round(score, 1)
        })

    df = pd.DataFrame(datos)
    # Doble seguridad: eliminar duplicados por columnas clave
    df = df.drop_duplicates(subset=['Partido', 'Hora', 'Liga'])
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
st.markdown("Selecciona una competencia para ver los partidos y picks")

for code, nombre in LIGAS.items():
    if st.button(nombre, key=f"btn_{code}", use_container_width=True):
        with st.spinner(f"Cargando {nombre}..."):
            matches, error = cargar_partidos_liga(code)
            if error:
                st.error(error)
                if "429" in error or "limit" in error:
                    st.warning("Límite de API alcanzado. Esperá 1 minuto y volvé a hacer clic.")
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
                st.warning("No hay partidos programados en el rango para esta competencia.")
