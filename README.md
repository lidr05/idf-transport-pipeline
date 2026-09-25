[English version below / Version française plus bas](#idf-transport-data-pipeline-version-française)

# IDF Transport Data Pipeline

This project is an end-to-end data engineering pipeline designed to ingest, process, and store real-time public transportation schedules for the Île-de-France region using the official Île-de-France Mobilités (Navitia) API.

## Architecture

```
PRIM API (Navitia)  →  Airflow DAG (every 5 min)  →  PostgreSQL  →  Streamlit dashboard
```

The project relies on a containerized, idempotent architecture:

* **Extraction:** A Python task queries the IDFM REST API every 5 minutes.
* **Orchestration:** Apache Airflow manages the DAG and its task dependencies (Ingestion > Row count > Obsolete data purge).
* **Storage:** A PostgreSQL database. Inserts use an upsert, so re-running the pipeline never creates duplicates.
* **Data Lifecycle:** Automated cleanup purges departed trains to keep the database lightweight and real-time.
* **Visualization:** A Streamlit web application providing a monitoring dashboard.

## Technical Stack

* **Language:** Python (Pandas, SQLAlchemy, Requests, Pytz, Streamlit)
* **Orchestration:** Apache Airflow
* **Database:** PostgreSQL
* **Infrastructure:** Docker & Docker Compose (Linux/WSL2 environments)

## Project Structure

```
idf-transport-pipeline/
├── dags/
│   └── transport_dag.py   # Airflow DAG: the production pipeline (runs in Docker)
├── app.py                 # Streamlit dashboard
├── search_station.py      # Utility: find a station ID from its name
├── pipeline.py            # Standalone ingestion, without Airflow (testing)
├── ingest.py              # API exploration: lists the network's lines
├── read_db.py             # Prints the table content in the terminal
├── docker-compose.yml     # Infrastructure: PostgreSQL (data), PostgreSQL (Airflow metadata), Airflow
├── requirements.txt       # Python dependencies for the scripts run locally
├── .env.example           # Configuration template, to copy to .env
├── .gitignore
└── README.md
```

Created locally and never versioned: `.env` (your configuration and API key), `venv/`, and the `logs/` and `plugins/` folders used by Airflow.

### Python scripts

| File | Role | Runs in |
|---|---|---|
| `dags/transport_dag.py` | The production pipeline. Every 5 minutes, Airflow runs three tasks in sequence: `ingest_data` fetches the next departures of the configured station, keeps only the target routes and upserts them into PostgreSQL; `count_rows` logs the table size; `cleanup_old_data` deletes departures whose time has passed. | Docker (Airflow) |
| `app.py` | Streamlit dashboard displaying the departures stored in the database. | Local |
| `search_station.py` | Searches a station by name and prints its Navitia ID (`stop_area:IDFM:...`), needed to configure the DAG. | Local |
| `pipeline.py` | Standalone, single-run version of the ingestion, without Airflow and without route filtering. Prints the departures and upserts them. Useful to test the API and database connections, or to see which route names are available at a station. | Local |
| `ingest.py` | Exploration script: lists the lines of the network (`/lines` endpoint). Does not write to the database. | Local |
| `read_db.py` | Prints the content of the `prochains_departs` table. | Local |

Scripts marked "Local" must be run from the project root, with the virtual environment from step 7 activated and the `.env` file filled in. `pipeline.py`, `read_db.py` and `app.py` also need the Docker stack running and the table created.

## Installation and Setup

### 1. Prerequisites

Ensure the following tools are installed on your machine:

* [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
* [Python 3.10+](https://www.python.org/downloads/)
* [Git](https://git-scm.com/downloads)

On Windows, run every command below from a WSL2 terminal.

### 2. Clone the repository

```bash
git clone https://github.com/lidr05/idf-transport-pipeline.git
cd idf-transport-pipeline
```

### 3. Configuration

1. Create an account on the [Île-de-France Mobilités API Portal](https://prim.iledefrance-mobilites.fr/fr).
2. Generate an API key from your account dashboard.
3. Copy the configuration template: `cp .env.example .env`
4. In `.env`, replace `votre_cle_api` with your API key, and replace `changeme` with a password of your choice. The password appears twice (`POSTGRES_PASSWORD` and `DATABASE_URL`) and must be identical in both. Avoid the characters `@ : / #`, since the password is inserted into a URL.

> **Important:** PostgreSQL only reads the password when the database is created for the first time. Set it before your first `docker compose up`. If you change it afterwards, see [Troubleshooting](#troubleshooting).

### 4. Start the infrastructure

Make sure Docker is running, then:

```bash
docker compose up -d
```

The first launch downloads the Docker images and can take a few minutes.

### 5. Create the table

Wait a few seconds for PostgreSQL to be ready, then open a SQL console:

```bash
docker exec -it idf_postgres psql -U admin -d transport_db
```

Run the following queries:

```sql
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

Exit the console with `\q`.

Alternatively, you can run these queries from any SQL client (e.g. SQLTools) connected to `localhost:5432`, with user `admin`, database `transport_db` and the password from your `.env`.

### 6. Start the pipeline in Airflow

1. Open the Airflow Web UI at `http://localhost:8080` and log in with username `airflow` and password `airflow`.
2. Unpause the `ingestion_transport_idf` DAG. A first run starts within moments, then every 5 minutes.

### 7. Launch the dashboard

Set up a local Python environment and run the Streamlit app:

```bash
python -m venv venv        # or: python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The dashboard is available at `http://localhost:8501`. It does not refresh on its own: reload the page to see the latest data.

## Monitoring another station

By default, the pipeline monitors **Marcadet-Poissonniers** (`stop_area:IDFM:71511`) and keeps only metro lines 4 and 12, identified by their terminus names. To monitor another station:

1. In `search_station.py`, set the `recherche` variable to the station name, then run `python search_station.py`. The script prints the matching stations and their IDs.
2. In `dags/transport_dag.py`, paste the ID into the `id_station` variable of the `ingest_data` function (and into `pipeline.py` if you use it).
3. In the same function, adjust the `lignes_cibles` list. The filter compares against the route name returned by the API. To see the route names available at your station, run `python pipeline.py` and look at the `ligne` column. Note that this script also writes those departures to the database; they are purged automatically once their time has passed.

The `dags/` folder is mounted into the Airflow containers, so Airflow picks up the modified DAG without a restart.

## Stopping the project

```bash
docker compose down      # stops the containers, keeps the data
docker compose down -v   # stops the containers and deletes the volumes (full reset: the table must be recreated)
```

## Troubleshooting

**The Airflow Web UI is not accessible**

```bash
docker compose down
mkdir -p dags logs plugins
sudo chmod -R 777 dags logs plugins
docker compose up airflow-init
docker compose up -d
```

**`password authentication failed for user "admin"`**

The password in `.env` does not match the one PostgreSQL was initialized with. Either restore the original password in `.env`, or reset the database with `docker compose down -v` followed by `docker compose up -d`, then recreate the table (step 5). Also check that `DATABASE_URL` has exactly one `:` between `admin` and the password.

**The `idf_postgres` container stops right after starting**

`POSTGRES_PASSWORD` is empty: the `.env` file is missing, empty, or not located at the project root. Check with `docker compose logs postgres`.

**Port 5432 is already in use**

Another PostgreSQL instance is running on your machine. Stop it, or change the port mapping in `docker-compose.yml` (e.g. `"5433:5432"`) and update the port in `DATABASE_URL` accordingly.

**API error 401 or 403**

The API key is invalid or missing. Check `PRIM_API_KEY` in `.env`. After any change to `.env`, run `docker compose up -d` again so that the containers pick up the new values.

**The dashboard shows an empty database**

Check that the DAG is unpaused and that its last run succeeded (task logs are available in the Airflow UI). The table can also legitimately be empty when no departure matches `lignes_cibles`, for instance at night when the metro is closed.

---

# IDF Transport Data Pipeline (Version Française)

Ce projet est un pipeline d'ingénierie des données de bout en bout permettant d'ingérer, de traiter et de stocker en temps réel les horaires de passage des transports franciliens via l'API officielle d'Île-de-France Mobilités (Navitia).

## Architecture

```
API PRIM (Navitia)  →  DAG Airflow (toutes les 5 min)  →  PostgreSQL  →  Tableau de bord Streamlit
```

Le projet repose sur une architecture conteneurisée et idempotente :

* **Extraction :** Une tâche Python interroge l'API REST IDFM toutes les 5 minutes.
* **Orchestration :** Apache Airflow gère le DAG et les dépendances entre tâches (Ingestion > Comptage > Purge des données obsolètes).
* **Stockage :** Base de données PostgreSQL. Les insertions se font par upsert : relancer le pipeline ne crée jamais de doublons.
* **Data Lifecycle :** Nettoyage automatisé des trains dont l'heure de départ est dépassée, pour maintenir une base légère et en temps réel.
* **Visualisation :** Une application web Streamlit fournissant un tableau de bord de suivi.

## Stack Technique

* **Langage :** Python (Pandas, SQLAlchemy, Requests, Pytz, Streamlit)
* **Orchestration :** Apache Airflow
* **Base de données :** PostgreSQL
* **Infrastructure :** Docker & Docker Compose (environnements Linux/WSL2)

## Arborescence du projet

```
idf-transport-pipeline/
├── dags/
│   └── transport_dag.py   # DAG Airflow : le pipeline de production (tourne dans Docker)
├── app.py                 # Tableau de bord Streamlit
├── search_station.py      # Utilitaire : trouver l'ID d'une station à partir de son nom
├── pipeline.py            # Ingestion autonome, sans Airflow (tests)
├── ingest.py              # Exploration de l'API : liste les lignes du réseau
├── read_db.py             # Affiche le contenu de la table dans le terminal
├── docker-compose.yml     # Infrastructure : PostgreSQL (données), PostgreSQL (métadonnées Airflow), Airflow
├── requirements.txt       # Dépendances Python des scripts lancés en local
├── .env.example           # Modèle de configuration, à copier en .env
├── .gitignore
└── README.md
```

Créés en local et jamais versionnés : `.env` (votre configuration et votre clé API), `venv/`, ainsi que les dossiers `logs/` et `plugins/` utilisés par Airflow.

### Scripts Python

| Fichier | Rôle | S'exécute dans |
|---|---|---|
| `dags/transport_dag.py` | Le pipeline de production. Toutes les 5 minutes, Airflow enchaîne trois tâches : `ingest_data` récupère les prochains départs de la station configurée, ne garde que les lignes ciblées et les insère par upsert dans PostgreSQL ; `count_rows` journalise le nombre de lignes de la table ; `cleanup_old_data` supprime les départs dont l'heure est passée. | Docker (Airflow) |
| `app.py` | Tableau de bord Streamlit affichant les départs stockés en base. | Local |
| `search_station.py` | Recherche une station par son nom et affiche son identifiant Navitia (`stop_area:IDFM:...`), nécessaire pour configurer le DAG. | Local |
| `pipeline.py` | Version autonome de l'ingestion, en une seule exécution, sans Airflow et sans filtre de lignes. Affiche les départs et les insère par upsert. Utile pour tester les connexions à l'API et à la base, ou pour voir les noms de lignes disponibles à une station. | Local |
| `ingest.py` | Script d'exploration : liste les lignes du réseau (endpoint `/lines`). N'écrit rien en base. | Local |
| `read_db.py` | Affiche le contenu de la table `prochains_departs`. | Local |

Les scripts marqués « Local » se lancent depuis la racine du projet, avec l'environnement virtuel de l'étape 7 activé et le fichier `.env` renseigné. `pipeline.py`, `read_db.py` et `app.py` nécessitent en plus que la stack Docker tourne et que la table soit créée.

## Installation et Configuration

### 1. Prérequis

Assurez-vous que les outils suivants sont installés sur votre machine :

* [Docker](https://docs.docker.com/get-docker/) et [Docker Compose](https://docs.docker.com/compose/install/)
* [Python 3.10+](https://www.python.org/downloads/)
* [Git](https://git-scm.com/downloads)

Sous Windows, lancez toutes les commandes ci-dessous depuis un terminal WSL2.

### 2. Cloner le dépôt

```bash
git clone https://github.com/lidr05/idf-transport-pipeline.git
cd idf-transport-pipeline
```

### 3. Configuration

1. Créez un compte sur le [Portail API Île-de-France Mobilités](https://prim.iledefrance-mobilites.fr/fr).
2. Générez une clé API depuis votre espace personnel.
3. Copiez le modèle de configuration : `cp .env.example .env`
4. Dans `.env`, remplacez `votre_cle_api` par votre clé API, et `changeme` par un mot de passe de votre choix. Le mot de passe apparaît deux fois (`POSTGRES_PASSWORD` et `DATABASE_URL`) et doit être identique aux deux endroits. Évitez les caractères `@ : / #`, car le mot de passe est inséré dans une URL.

> **Important :** PostgreSQL ne lit le mot de passe qu'à la toute première création de la base. Définissez-le avant votre premier `docker compose up`. Pour le changer ensuite, voir la section [Dépannage](#dépannage).

### 4. Lancer l'infrastructure

Vérifiez que Docker est démarré, puis :

```bash
docker compose up -d
```

Le premier lancement télécharge les images Docker et peut prendre quelques minutes.

### 5. Créer la table

Attendez quelques secondes que PostgreSQL soit prêt, puis ouvrez une console SQL :

```bash
docker exec -it idf_postgres psql -U admin -d transport_db
```

Exécutez les requêtes suivantes :

```sql
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

Quittez la console avec `\q`.

Vous pouvez aussi exécuter ces requêtes depuis n'importe quel client SQL (ex. : SQLTools) connecté à `localhost:5432`, avec l'utilisateur `admin`, la base `transport_db` et le mot de passe de votre `.env`.

### 6. Démarrer le pipeline dans Airflow

1. Ouvrez l'interface web d'Airflow sur `http://localhost:8080` et connectez-vous avec l'identifiant `airflow` et le mot de passe `airflow`.
2. Activez (*Unpause*) le DAG `ingestion_transport_idf`. Une première exécution démarre dans les instants qui suivent, puis toutes les 5 minutes.

### 7. Lancer le tableau de bord

Configurez un environnement Python local et lancez l'application Streamlit :

```bash
python -m venv venv        # ou : python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Le tableau de bord est accessible sur `http://localhost:8501`. Il ne se rafraîchit pas tout seul : rechargez la page pour voir les dernières données.

## Suivre une autre station

Par défaut, le pipeline suit la station **Marcadet-Poissonniers** (`stop_area:IDFM:71511`) et ne garde que les métros 4 et 12, identifiés par le nom de leurs terminus. Pour suivre une autre station :

1. Dans `search_station.py`, remplacez la valeur de la variable `recherche` par le nom de la station, puis lancez `python search_station.py`. Le script affiche les stations correspondantes et leurs identifiants.
2. Dans `dags/transport_dag.py`, collez l'identifiant dans la variable `id_station` de la fonction `ingest_data` (ainsi que dans `pipeline.py` si vous l'utilisez).
3. Dans la même fonction, adaptez la liste `lignes_cibles`. Le filtre porte sur le nom de ligne (*route*) renvoyé par l'API. Pour connaître les noms disponibles à votre station, lancez `python pipeline.py` et regardez la colonne `ligne`. Attention : ce script écrit aussi ces départs en base ; ils seront purgés automatiquement une fois leur heure passée.

Le dossier `dags/` est monté dans les conteneurs Airflow : Airflow prend en compte le DAG modifié sans redémarrage.

## Arrêter le projet

```bash
docker compose down      # arrête les conteneurs, conserve les données
docker compose down -v   # arrête les conteneurs et supprime les volumes (remise à zéro complète : la table devra être recréée)
```

## Dépannage

**L'interface web d'Airflow n'est pas accessible**

```bash
docker compose down
mkdir -p dags logs plugins
sudo chmod -R 777 dags logs plugins
docker compose up airflow-init
docker compose up -d
```

**`password authentication failed for user "admin"`**

Le mot de passe du `.env` ne correspond pas à celui avec lequel PostgreSQL a été initialisé. Remettez l'ancien mot de passe dans `.env`, ou réinitialisez la base avec `docker compose down -v` puis `docker compose up -d`, et recréez la table (étape 5). Vérifiez aussi que `DATABASE_URL` contient exactement un `:` entre `admin` et le mot de passe.

**Le conteneur `idf_postgres` s'arrête juste après son démarrage**

`POSTGRES_PASSWORD` est vide : le fichier `.env` est absent, vide, ou n'est pas à la racine du projet. Vérifiez avec `docker compose logs postgres`.

**Le port 5432 est déjà utilisé**

Une autre instance PostgreSQL tourne sur votre machine. Arrêtez-la, ou changez le port exposé dans `docker-compose.yml` (ex. : `"5433:5432"`) et mettez à jour le port dans `DATABASE_URL`.

**Erreur 401 ou 403 de l'API**

La clé API est invalide ou absente. Vérifiez `PRIM_API_KEY` dans `.env`. Après toute modification du `.env`, relancez `docker compose up -d` pour que les conteneurs prennent en compte les nouvelles valeurs.

**Le tableau de bord indique une base vide**

Vérifiez que le DAG est activé et que sa dernière exécution a réussi (les logs des tâches sont consultables dans l'interface Airflow). La table peut aussi être vide tout à fait normalement si aucun départ ne correspond à `lignes_cibles`, par exemple la nuit quand le métro est fermé.
