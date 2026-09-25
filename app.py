import os
from dotenv import load_dotenv
import streamlit as st
import pandas as pd

from sqlalchemy import create_engine

st.set_page_config(page_title="IDF Transports", layout="centered")
st.title("Prochains Départs - IDF Transport")
st.markdown("Dashboard : prochains départs de la station concernée dans la base de données.")

load_dotenv()

@st.cache_resource
def init_db_connection():
    return create_engine(os.getenv("DATABASE_URL"))

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