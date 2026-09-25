import os 
import requests
import pandas as pd

from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import pytz
from airflow import DAG
from airflow.operators.python import PythonOperator 

from dotenv import load_dotenv

load_dotenv()

def ingest_data():
    api_key = os.getenv("PRIM_API_KEY")
    db_url = os.getenv("DATABASE_URL")

    headers = { "apiKey" : api_key }

    # ID trouvé par search_station.py pour la station "Marcadet-Poissoniers"
    id_station = "stop_area:IDFM:71511" 
    url = f"https://prim.iledefrance-mobilites.fr/marketplace/v2/navitia/stop_areas/{id_station}/departures"

    reponse = requests.get(url, headers=headers)
    if reponse.status_code == 200:
        data = reponse.json()

        # Exemples : Terminus métro 4 et 12
        lignes_cibles = [
            "Mairie d'Aubervilliers",
            "Mairie d'Issy", 
            "Bagneux", 
            "Porte de Clignancourt"  
            ] # Remplacez par les Terminus que vous souhaitez filtrer
        
        departures = data.get("departures", [])

        lignes_propres = []
        heure_insertion = datetime.now()
        for departure in departures:
            nom_ligne = departure["route"]["name"]
            if nom_ligne in lignes_cibles:
                lignes_propres.append({
                    "station_id": id_station,
                    "ligne": nom_ligne,
                    "direction": departure["display_informations"]["direction"],
                    "heure_depart_prevue": departure["stop_date_time"]["departure_date_time"],
                    "date_insertion": heure_insertion
                })
        df = pd.DataFrame(lignes_propres)
        
        if not df.empty:
            engine = create_engine(db_url)

            # Requête d'upsert pour éviter les doublons
            upsert_query = text("""
                INSERT INTO prochains_departs (station_id, ligne, direction, heure_depart_prevue, date_insertion)
                VALUES (:station_id, :ligne, :direction, :heure_depart_prevue, :date_insertion)
                ON CONFLICT (station_id, ligne, direction, heure_depart_prevue)
                DO UPDATE SET date_insertion = EXCLUDED.date_insertion
            """)

            with engine.begin() as conn:
                for ligne in lignes_propres:
                    conn.execute(upsert_query, ligne)
            print("Données insérées avec succès dans la base de données. (UPSERT)")

        else:
            print("Aucune donnée à insérer.")
    else:
        raise Exception(f"Erreur lors de la requête : {reponse.status_code}, {reponse.text}")

def count_rows():
    db_url = os.getenv("DATABASE_URL")
    engine = create_engine(db_url)
    df_count = pd.read_sql("SELECT COUNT(*) FROM prochains_departs", engine)

    print(f"Nombre de lignes dans la table : {df_count.iloc[0, 0]}")

def cleanup_old_data():
    db_url = os.getenv("DATABASE_URL")
    engine = create_engine(db_url)

    timezone = pytz.timezone('Europe/Paris')
    current_time = datetime.now(timezone)
    current_time_str = current_time.strftime('%Y%m%dT%H%M%S')

    query = text("DELETE FROM prochains_departs WHERE heure_depart_prevue < :now")
    with engine.begin() as conn:  
        result = conn.execute(query, {"now": current_time_str})
        print(f"Nombre d'anciens départs supprimés : {result.rowcount}")

# Config du DAG
default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}
with DAG(
    dag_id='ingestion_transport_idf',
    default_args=default_args,
    start_date=datetime(2023, 1, 1),
    schedule_interval=timedelta(minutes=5),
    catchup=False,
    tags=['transports', 'idf']
) as dag:
    ingest_task = PythonOperator(
        task_id='ingest_data',
        python_callable=ingest_data
    )

    count_task = PythonOperator(
        task_id='count_rows',
        python_callable=count_rows
    )

    cleanup_task = PythonOperator(
        task_id='cleanup_old_data',
        python_callable=cleanup_old_data
    )

    ingest_task >> count_task >> cleanup_task
