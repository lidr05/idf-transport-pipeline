[English/French Version Available Below]

# IDF Transport Data Pipeline

This project is an end-to-end data engineering pipeline designed to ingest, process, and store real-time public transportation schedules for the Île-de-France region using the official Île-de-France Mobilités (Navitia) API.

## Architecture

The project relies on a containerized, idempotent architecture:

* **Extraction:** A Python script queries the IDFM REST API every 5 minutes.
* **Orchestration:** Apache Airflow manages the DAG ensuring task dependencies (Ingestion > Obsolete Data Purge).
* **Storage:** A PostgreSQL database.
* **Data Lifecycle:** Automated cleanup processes purge departed trains to maintain a lightweight, real-time database.
* **Visualization:** A Streamlit web application providing a real-time monitoring dashboard.

## Technical Stack

* **Language:** Python (Pandas, SQLAlchemy, Requests, Streamlit)
* **Orchestration:** Apache Airflow
* **Database:** PostgreSQL
* **Infrastructure:** Docker & Docker Compose (Linux/WSL2 environments)

## Installation and Setup

### 1. Prerequisites

Ensure the following tools are installed on your machine:

* [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
* [Python 3.8+](https://www.python.org/downloads/)
* [Git](https://git-scm.com/downloads)

### 2. Get an IDFM API Key

1. Create an account on the [Île-de-France Mobilités API Portal](https://prim.iledefrance-mobilites.fr/fr).
2. Generate an API Key from your dashboard.
3. Open the `dags/transport_dag.py` file and replace the placeholder with your generated key in the `ingest_data` function.

### 3. Deployment

Clone the repository and launch the Docker infrastructure:

```bash
git clone git@github.com:lidr05/idf-transport-pipeline.git
cd idf-transport-pipeline
docker compose up -d
```

### 4. Initialization
### Create the table first : 
```bash
docker exec -it idf_postgres psql -U admin -d transport_db
```
And then :
```bash
CREATE TABLE IF NOT EXISTS prochains_departs (
    station_id VARCHAR(50),
    ligne VARCHAR(255),
    direction VARCHAR(255),
    heure_depart_prevue VARCHAR(50),
    date_insertion TIMESTAMP
);

ALTER TABLE prochains_departs 
ADD CONSTRAINT unique_train_departure UNIQUE (station_id, ligne, direction, heure_depart_prevue);
```
And finally :
```bash
\q
```
Then : 
1. Access the Airflow Web UI at `http://localhost:8080`.
2. Unpause the `ingestion_transport_idf` DAG to start the automated data pipeline.
3. (Optional) Run the PostgreSQL table creation and constraint queries via your preferred SQL client (e.g., SQLTools) mapped to `localhost:5432`.

If the Web UI is not accessible :
```bash
docker compose down
mkdir -p dags logs plugins
sudo chmod -R 777 dags logs plugins
docker compose up airflow-init
docker compose up -d
```
### 5. Launch the Dashboard

To visualize the real-time data, set up a local Python environment and run the Streamlit app:

```bash
python -m venv venv # Or python3 -m venv venv 
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install streamlit pandas sqlalchemy psycopg2-binary pytz
streamlit run app.py
```

The dashboard will be available at `http://localhost:8501`.

---

# IDF Transport Data Pipeline (Version Française)

Ce projet est un pipeline d'ingénierie des données de bout en bout permettant d'ingérer, de traiter et de stocker en temps réel les horaires de passages des transports franciliens via l'API officielle d'Île-de-France Mobilités (Navitia).

## Architecture

Le projet repose sur une architecture conteneurisée et idempotente :

* **Extraction :** Un script Python interroge l'API REST IDFM toutes les 5 minutes.
* **Orchestration :** Apache Airflow gère le DAG assurant les dépendances (Ingestion > Purge des données obsolètes).
* **Stockage :** Base de données PostgreSQL.
* **Data Lifecycle :** Nettoyage automatisé des trains dont l'heure de départ est dépassée pour maintenir une base en temps réel.
* **Visualisation :** Une application web Streamlit fournissant un tableau de bord de suivi en direct.

## Stack Technique

* **Langage :** Python (Pandas, SQLAlchemy, Requests, Pytz, Streamlit)
* **Orchestration :** Apache Airflow
* **Base de données :** PostgreSQL
* **Infrastructure :** Docker & Docker Compose (Environnements Linux/WSL2)

## Installation et Configuration

### 1. Prérequis

Assurez-vous que les outils suivants sont installés sur votre machine :

* [Docker](https://docs.docker.com/get-docker/) et [Docker Compose](https://docs.docker.com/compose/install/)
* [Python 3.8+](https://www.python.org/downloads/)
* [Git](https://git-scm.com/downloads)

### 2. Obtenir une clé API IDFM

1. Créez un compte sur le [Portail API Île-de-France Mobilités](https://prim.iledefrance-mobilites.fr/fr).
2. Générez une clé API depuis votre espace personnel.
3. Ouvrez le fichier `dags/transport_dag.py` et remplacez la valeur générique par votre clé dans la fonction `ingest_data`.

### 3. Déploiement

Clonez le dépôt et lancez l'infrastructure Docker :

```bash
git clone git@github.com:lidr05/idf-transport-pipeline.git
cd idf-transport-pipeline
docker compose up -d
```

### 4. Initialisation
#### Créer la table en premier lieu : 
```bash
docker exec -it idf_postgres psql -U admin -d transport_db
```
Puis :
```bash
CREATE TABLE IF NOT EXISTS prochains_departs (
    station_id VARCHAR(50),
    ligne VARCHAR(255),
    direction VARCHAR(255),
    heure_depart_prevue VARCHAR(50),
    date_insertion TIMESTAMP
);

ALTER TABLE prochains_departs 
ADD CONSTRAINT unique_train_departure UNIQUE (station_id, ligne, direction, heure_depart_prevue);
```
Et enfin :
```bash
\q
```
Ensuite : 
1. Accédez à l'interface web d'Airflow via `http://localhost:8080`.
2. Activez (Unpause) le DAG `ingestion_transport_idf` pour lancer l'automatisation.
3. (Optionnel) Exécutez les requêtes SQL de création de table et de contraintes d'unicité via votre client SQL (ex: SQLTools) connecté sur `localhost:5432`.

Si l'interface web n'est pas accessible :
```bash
docker compose down
mkdir -p dags logs plugins
sudo chmod -R 777 dags logs plugins
docker compose up airflow-init
docker compose up -d
```
### 5. Lancer le Tableau de Bord

Pour visualiser les données en temps réel, configurez un environnement Python local et lancez l'application Streamlit :

```bash
python -m venv venv # Ou python3 -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate
pip install streamlit pandas sqlalchemy psycopg2-binary pytz
streamlit run app.py
```

Le tableau de bord sera accessible à l'adresse `http://localhost:8501`.
