import streamlit as st
import pandas as pd
import pytz

from sqlalchemy import create_engine
from datetime import datetime

st.set_page_config(page_title="IDF Transports", layout="centered")
st.title("Prochains Départs - IDF Transport")
st.markdown("Dashboard : prochains départs dans les 5 prochaines minutes de la station concernée.")

@st.cache_resource
def init_db_connection():
    return create_engine("postgresql://admin:secretpassword@localhost:5432/transport_db")

engine = init_db_connection()

query = "SELECT * FROM prochains_departs ORDER BY heure_depart_prevue ASC"
try:
    df = pd.read_sql(query, engine)
    if not df.empty:
        # Nettoyage de l'affichage de l'heure
        df['heure_depart'] = pd.to_datetime(df['heure_depart_prevue']).dt.strftime('%H:%M:%S')

        # Colonnes à afficher
        df_display = df[['ligne', 'direction', 'heure_depart']]
        df_display.columns = ['Ligne', 'Direction', 'Heure de départ']

        st.dataframe(df_display, use_container_width=True, hide_index=True)

        # Visuel additionnel
        st.info(f"Volume actuel : {len(df)} départs programmés dans la base.")
    else:
        st.warning("Base de données vide. / Aucun départ trouvé dans la base de données.")

except Exception as e:
    st.error(f"Erreur lors de la connexion à la base : {e}")