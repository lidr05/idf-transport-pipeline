# IDF Transport Data Pipeline

Ce projet est un pipeline d'ingénierie des données de bout en bout permettant d'ingérer, de nettoyer et de stocker en temps réel les horaires de passages des transports franciliens via l'API officielle d'Île-de-France Mobilités (Navitia).

## Architecture

![Architecture du Pipeline](lien_vers_ton_image.png)

Le projet repose sur une architecture conteneurisée :
* **Extraction :** Script Python interrogeant l'API REST IDFM toutes les 5 minutes.
* **Orchestration :** Apache Airflow (Docker) gérant le DAG des tâches (Ingestion > Dédoublonnage > Purge).
* **Stockage :** Base de données PostgreSQL (Docker).
* **Data Lifecycle :** Nettoyage automatisé des trains obsolètes pour maintenir une base en temps réel.

## Stack Technique
* **Langage :** Python (Pandas, SQLAlchemy, requests)
* **Orchestration :** Apache Airflow
* **Base de données :** PostgreSQL
* **Infrastructure :** Docker & Docker Compose sur environnement Linux (WSL2)

## Démarrage Rapide
1. Cloner le dépôt : `git clone git@github.com:lidr05/idf-transport-pipeline.git`
2. Ajouter la clé API IDFM dans le DAG.
3. Lancer l'infrastructure : `docker-compose up -d`
4. Accéder à Airflow via `http://localhost:8080`
