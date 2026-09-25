import os
import requests
from dotenv import load_dotenv

# Chargement de la clé API depuis le fichier .env
load_dotenv()
api_key = os.getenv("PRIM_API_KEY")

# Préparation du header
headers = { "apiKey" : api_key }

recherche = "Marcadet-Poissoniers"  # Remplacez par le nom de la station que vous souhaitez rechercher
url = "https://prim.iledefrance-mobilites.fr/marketplace/v2/navitia/places"

# Récupération des données
print("Envoi de la requête à l'API...")
reponse = requests.get(url, headers=headers, params={"q": recherche})

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