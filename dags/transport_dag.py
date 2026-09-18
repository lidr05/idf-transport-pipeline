import os 
import requests
import pandas as pd

from sqlalchemy import create_engine
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator 

# Ancien script
def ingest_data():
    api_key =  # Remplacez par votre clé API réelle
    db_url = "postgresql://admin:secretpassword@idf_postgres:5432/transport_db"

    headers = { "apiKey" : api_key }
    id_station = "stop_area:IDFM:71321" 
    url = f"https://prim.iledefrance-mobilites.fr/marketplace/v2/navitia/stop_areas/{id_station}/departures"

    reponse = requests.get(url, headers=headers)
    if reponse.status_code == 200:
        data = reponse.json()
        departures = data.get("departures", [])

        lignes_propres = []
        heure_insertion = datetime.now()
        for departure in departures:
                lignes_propres.append({
                    "station_id": id_station,
                    "ligne": departure["route"]["name"],
                    "direction": departure["display_informations"]["direction"],
                    "heure_depart_prevue": departure["stop_date_time"]["departure_date_time"],
                    "date_insertion": heure_insertion
                })
        df = pd.DataFrame(lignes_propres)
        if not df.empty:
            engine = create_engine(db_url)
            df.to_sql('prochains_departs', engine, if_exists='append', index=False)
            print("Données insérées avec succès dans la base de données.")
        else:
            print("Aucune donnée à insérer.")
    else:
        raise Exception(f"Erreur lors de la requête : {reponse.status_code}, {reponse.text}")

def count_rows():
    db_url = "postgresql://admin:secretpassword@idf_postgres:5432/transport_db"
    engine = create_engine(db_url)
    df_count = pd.read_sql("SELECT COUNT(*) FROM prochains_departs", engine)

    print(f"Nombre de lignes dans la table : {df_count.iloc[0, 0]}")

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

    ingest_task >> count_task
