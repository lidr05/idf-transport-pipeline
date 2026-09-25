import os
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import requests

from sqlalchemy import create_engine

st.set_page_config(page_title="IDF Transports", layout="centered")
st.title("Prochains Départs - IDF Transport")
st.markdown("Dashboard : prochains départs des stations suivies, tels qu'enregistrés dans la base de données.")

load_dotenv()

@st.cache_resource
def init_db_connection():
    return create_engine(os.getenv("DATABASE_URL"))

@st.cache_data(ttl=24 * 3600)
def get_station_name(station_id):
    """Récupère le nom d'une station via l'API PRIM à partir de son ID (résultat gardé en cache 24 h)."""
    url = f"https://prim.iledefrance-mobilites.fr/marketplace/v2/navitia/stop_areas/{station_id}"
    reponse = requests.get(url, headers={"apiKey": os.getenv("PRIM_API_KEY")}, timeout=5)
    reponse.raise_for_status()
    return reponse.json()["stop_areas"][0]["name"]

def nom_affichable(station_id):
    """Nom de la station si l'API répond, sinon son identifiant (un échec n'est pas mis en cache)."""
    try:
        return get_station_name(station_id)
    except Exception:
        return station_id

engine = init_db_connection()

query = "SELECT * FROM prochains_departs ORDER BY heure_depart_prevue ASC"
try:
    df = pd.read_sql(query, engine)
    if not df.empty:
        # Nettoyage de l'affichage de l'heure
        df['heure_depart'] = pd.to_datetime(df['heure_depart_prevue']).dt.strftime('%H:%M:%S')

        # Un tableau par station (utile juste après un changement de station,
        # tant que les départs de l'ancienne n'ont pas été purgés)
        for station_id, df_station in df.groupby('station_id'):
            st.subheader(f" {nom_affichable(station_id)}")

            df_display = df_station[['ligne', 'direction', 'heure_depart']]
            df_display.columns = ['Ligne', 'Direction', 'Heure de départ']
            st.dataframe(df_display, width="stretch", hide_index=True)

        # Visuel additionnel
        st.info(f"Volume actuel : {len(df)} départs programmés dans la base.")
    else:
        st.warning("Base de données vide. / Aucun départ trouvé dans la base de données.")

except Exception as e:
    st.error(f"Erreur lors de la connexion à la base : {e}")
