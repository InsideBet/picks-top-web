import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import os
from pathlib import Path

# ────────────────────────────────────────────────
# CONFIGURACIÓN
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="InsideBet",
    layout="wide"
)

# API Football
API_KEY_AF = st.secrets["API_KEY_AF"] # Tu key de API-Football
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
    "PL": "https://i.postimg.cc/7PcwYbk1/1.png",
    "PD": "https://i.postimg.cc/75d5mMQ2/8.png",
    "SA": "https://i.postimg.cc/mzxTFmpm/4.png",
    "FL1": "https://i.postimg.cc/jnbqBMz2/2.png",
    "BL1": "https://i.postimg.cc/5X09cYFn/3.png",
    "PPL": "https://i.postimg.cc/ZBr4P61R/5.png",
    "DED": "https://i.postimg.cc/tnkbwpqv/6.png",
    "CL": "https://i.postimg.cc/zb1V1DNy/7.png"
}
DIAS_FUTUROS = 2

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

def procesar_fixtures(fixtures):
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

# ────────────────────────────────────────────────
# RUTAS PARA GITHUB / STREAMLIT CLOUD (archivos subidos manualmente)
# ────────────────────────────────────────────────
RUTA_DATOS_FBREF = "datos_fbref"                     # carpeta en la raíz del repo
RUTA_EQUIPOS_FBREF = os.path.join(RUTA_DATOS_FBREF, "Ligas_Equipos")

@st.cache_data(ttl=1800)
def cargar_resumen_fbref():
    ruta = os.path.join(RUTA_DATOS_FBREF, "RESUMEN_STATS_Premier_League.xlsx")
    if not os.path.exists(ruta):
        return None, f"No se encontró {ruta} en el repositorio. Subilo manualmente a GitHub."
    try:
        return pd.read_excel(ruta), None
    except Exception as e:
        return None, f"Error al leer resumen: {str(e)}"

@st.cache_data(ttl=1800)
def cargar_cartelera_fbref():
    ruta = os.path.join(RUTA_DATOS_FBREF, "CARTELERA_PROXIMOS_Premier_League.xlsx")
    if not os.path.exists(ruta):
        return None, f"No se encontró {ruta} en el repositorio. Subilo manualmente."
    try:
        return pd.read_excel(ruta), None
    except Exception as e:
        return None, f"Error al leer cartelera: {str(e)}"

@st.cache_data(ttl=1800)
def listar_equipos_fbref():
    if not os.path.exists(RUTA_EQUIPOS_FBREF):
        return []
    return [
        f.replace('.xlsx', '').replace('_', ' ')
        for f in os.listdir(RUTA_EQUIPOS_FBREF)
        if f.endswith('.xlsx')
    ]

@st.cache_data(ttl=1800)
def cargar_excel_equipo_fbref(nombre_equipo):
    nombre_archivo = nombre_equipo.replace(' ', '_') + '.xlsx'
    ruta = os.path.join(RUTA_EQUIPOS_FBREF, nombre_archivo)
    if not os.path.exists(ruta):
        return None, f"No se encontró {nombre_archivo} en datos_fbref/Ligas_Equipos"
    try:
        excel = pd.ExcelFile(ruta)
        datos = {}
        for sheet in excel.sheet_names:
            datos[sheet] = excel.parse(sheet)
        return datos, None
    except Exception as e:
        return None, f"Error al leer {nombre_equipo}: {str(e)}"

# ────────────────────────────────────────────────
# INTERFAZ STREAMLIT
# ────────────────────────────────────────────────
tab_objects = st.tabs(list(LIGAS.values())) # crea los tabs
for i, (code, nombre) in enumerate(LIGAS.items()):
    with tab_objects[i]: # usamos el índice para acceder al tab correcto
        st.markdown(f"""
        <div style="display:flex; align-items:center; color:#e5e7eb; font-size:22px; font-weight:500; margin-bottom:10px;">
            <img src="{BANDERAS[code]}" width="30" style="vertical-align:middle; margin-right:10px;">
            <span>{nombre}</span>
        </div>
        """, unsafe_allow_html=True)
        
        if code == "PL":
            # ── Sección combinada: API-Football + FBRef ──
            col1, col2 = st.columns([3, 2])

            with col1:
                st.subheader("Próximos Partidos (API-Football)")
                fixtures_af, error_af = cargar_fixtures_af(LIGAS_AF_ID[code])
                if error_af:
                    st.error(f"API-Football: {error_af}")
                df_af = procesar_fixtures(fixtures_af) if fixtures_af else pd.DataFrame()
                if "Score" not in df_af.columns:
                    df_af["Score"] = 0
                df_af = df_af.sort_values("Score", ascending=False)
                if df_af.empty:
                    st.warning("No hay partidos programados en el rango seleccionado.")
                else:
                    st.dataframe(
                        df_af,
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
                    st.success(f"{len(df_af)} partidos encontrados.")

            with col2:
                st.subheader("Datos FBRef (scrapeados)")
                if st.button("🔄 Recargar / Verificar FBRef", key="reload_fbref"):
                    st.rerun()  # simple refresh

                # Debug temporal (podés quitar después de probar)
                st.caption(f"Directorio actual: {os.getcwd()}")
                st.caption(f"¿Existe 'datos_fbref'? {os.path.exists('datos_fbref')}")
                if os.path.exists('datos_fbref'):
                    st.caption(f"Contenido de datos_fbref: {os.listdir('datos_fbref')}")

                df_resumen, err_res = cargar_resumen_fbref()
                if df_resumen is not None:
                    st.caption("Estadísticas generales de equipos (xG, posesión, etc.)")
                    st.dataframe(df_resumen.head(10), use_container_width=True, hide_index=True)
                else:
                    st.info(err_res or "Resumen FBRef no encontrado – subilo a /datos_fbref/")

                df_cart, err_cart = cargar_cartelera_fbref()
                if df_cart is not None and not df_cart.empty:
                    st.caption("Próximos partidos según FBRef")
                    st.dataframe(df_cart.head(8), use_container_width=True, hide_index=True)
                else:
                    st.info(err_cart or "Cartelera FBRef no encontrada")

            # Selector de equipo (abajo)
            st.markdown("---")
            st.subheader("Estadísticas por equipo (FBRef)")
            equipos = listar_equipos_fbref()
            if equipos:
                equipo_sel = st.selectbox("Elige equipo", ["-- Selecciona --"] + sorted(equipos))
                if equipo_sel != "-- Selecciona --":
                    datos_eq, err_eq = cargar_excel_equipo_fbref(equipo_sel)
                    if datos_eq:
                        for sheet, df_sheet in datos_eq.items():
                            st.caption(f"{equipo_sel} → {sheet}")
                            st.dataframe(df_sheet, use_container_width=True, hide_index=True)
                    else:
                        st.error(err_eq)
            else:
                st.info("No hay Excels por equipo en /datos_fbref/Ligas_Equipos – subilos manualmente")

        else:
            # Lógica original para otras ligas
            fixtures_af, error_af = cargar_fixtures_af(LIGAS_AF_ID[code])
            if error_af:
                st.error(f"API-Football: {error_af}")
            df_af = procesar_fixtures(fixtures_af) if fixtures_af else pd.DataFrame()
            if "Score" not in df_af.columns:
                df_af["Score"] = 0
            df_af = df_af.sort_values("Score", ascending=False)
            if df_af.empty:
                st.warning("No hay partidos programados en el rango seleccionado.")
            else:
                st.dataframe(
                    df_af,
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
                st.success(f"{len(df_af)} partidos encontrados.")
