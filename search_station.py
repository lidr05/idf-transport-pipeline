import os
import requests
import pandas as pd
from dotenv import load_dotenv

# Chargement de la clé API depuis le fichier .env
load_dotenv()
api_key = os.getenv("PRIM_API_KEY")

# Préparation du header
headers = { "apiKey" : api_key }

recherche = "Avenue Foch"
url = f"https://prim.iledefrance-mobilites.fr/marketplace/v2/navitia/places?q={recherche}"

# Récupération des données
print("Envoi de la requête à l'API...")
reponse = requests.get(url, headers=headers)

if reponse.status_code == 200:
    data = reponse.json()

    for place in data.get("places", []):
        if place.get("embedded_type") == "stop_area":
            nom_station = place["name"]
            id_station = place["id"]
            print(f"Station : {nom_station}, ID de la station : {id_station}")
            print("-" * 30)

else:
    print(f"Erreur lors de la requête : {reponse.status_code}")
    print("Logs erreur:", reponse.text)
    data = None