import os
import requests
import pandas as pd
from dotenv import load_dotenv

# Chargement de la clé API depuis le fichier .env
load_dotenv()
api_key = os.getenv("PRIM_API_KEY")

# Préparation du header
headers = { "apiKey" : api_key }

url = "https://prim.iledefrance-mobilites.fr/marketplace/v2/navitia/lines"

# Récupération des données
print("Envoi de la requête à l'API...")
reponse = requests.get(url, headers=headers)

if reponse.status_code == 200:
    data = reponse.json()

    # Isolation + Transformation de la liste des lignes du JSON
    lines = data.get("lines", [])
    df = pd.DataFrame(lines)

    # Extraction du nom du réseau depuis la colonne 'network' 
    df['nom_reseau'] = df['network'].apply(lambda x: x.get('name') if isinstance(x, dict) else None)
    df_cleaned = df[ ['id', 'name', 'code', 'nom_reseau'] ]

    # Vérification et taille du tableau total
    print("Aperçu des données extraites :")
    print(df_cleaned.head())
    print("Nombre de lignes extraites : ", len(df_cleaned))

else:
    print(f"Erreur lors de la requête : {reponse.status_code}")
    print("Logs erreur:", reponse.text)
    data = None