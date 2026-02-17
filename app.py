import streamlit as st
import pandas as pd

st.set_page_config(page_title="Futbol Picks - Maico", layout="wide")

st.title("⚽ Futbol Picks - Próximos Partidos")
st.markdown("Versión beta - Picks basados en datos históricos")

# Datos de ejemplo (después lo reemplazamos con tu bot real)
data = {
    "Liga": ["Premier League", "Champions League", "La Liga"],
    "Hora": ["16:00", "20:45", "21:00"],
    "Partido": ["Man City vs Arsenal", "Real Madrid vs Bayern", "Barcelona vs Atletico"],
    "BTTS": ["Yes (68%)", "No (45%)", "Yes (72%)"],
    "Corners": ["Over 10.5", "Under 9.5", "Over 11.5"],
    "Tarjetas": ["Over 4.5", "Under 5.5", "Over 5.5"],
    "O/U 2.5": ["Over", "Under", "Over"],
    "Top Pick": ["BTTS Yes 🔥", "Under 2.5", "Over 2.5 🔥"]
}

df = pd.DataFrame(data)

st.dataframe(
    df.style.set_properties(**{'text-align': 'center', 'font-size': '14px'}),
    use_container_width=True,
    hide_index=True
)

st.markdown("**Top Pick del día**: BTTS Yes en Man City vs Arsenal (alta confianza histórica)")
st.markdown("Más detalles en VIP → [link a Telegram privado]")
