import os 
import requests
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime

# Chargement de API/DB
load_dotenv()
api_key = os.getenv("PRIM_API_KEY")
db_url = os.getenv("DATABASE_URL")

headers = { "apiKey" : api_key }
id_station = "stop_area:IDFM:71511" # Résultat de search_station.py
url = f"https://prim.iledefrance-mobilites.fr/marketplace/v2/navitia/stop_areas/{id_station}/departures"

print("Extraction des données:")
reponse = requests.get(url, headers=headers)
if reponse.status_code == 200:
    data = reponse.json()
    departs = data.get("departures", [])
    print(f"departs: {departs}")

    lignes_propres = []
    for dep in departs:
        lignes_propres.append({
            "station_id": id_station,
            "ligne": dep["route"]["name"],
            "direction": dep["display_informations"]["direction"],
            "heure_depart_prevue": dep["stop_date_time"]["departure_date_time"],
            "date_insertion": datetime.now()
        })
    df = pd.DataFrame(lignes_propres)
    print(df)

    if not df.empty:
        # Chargement vers PostgreSQL
        engine = create_engine(db_url)
        upsert_query = text("""
            INSERT INTO prochains_departs (station_id, ligne, direction, heure_depart_prevue, date_insertion)
            VALUES (:station_id, :ligne, :direction, :heure_depart_prevue, :date_insertion)
            ON CONFLICT (station_id, ligne, direction, heure_depart_prevue)
            DO UPDATE SET date_insertion = EXCLUDED.date_insertion
         """)

        with engine.begin() as conn:
            for ligne in lignes_propres:
                conn.execute(upsert_query, ligne)
        print(f"{len(df)} lignes insérées dans la base de données.")

    else :
        print("Aucun départ trouvé pour la station spécifiée.")

else:
    print(f"Erreur lors de la requête : {reponse.status_code}")
    print("Logs erreur:", reponse.text)
    data = None