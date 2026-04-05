# NWSL Roster API Overview
REST API built with FastAPI, PostgreSQL, and Apache Kafka.

Stack: Python · FastAPI · SQLAlchemy · PostgreSQL · Apache Kafka · Airflow · Docker
Features:
- Full CRUD REST API with OpenAPI documentation
- PostgreSQL backend with SQLAlchemy ORM
- Kafka event publishing on player mutations
- Airflow DAGs for roster workflow automation
- Pydantic models for request validation


# NWSL Roster API

A production-pattern REST API for NWSL team rosters, built with **FastAPI**, **PostgreSQL**, **Apache Kafka**, and **Apache Airflow**. Demonstrates a full modern Python backend stack including event-driven architecture, database persistence, workflow orchestration, and automatic OpenAPI documentation.

---

## Stack

| Component | Purpose | Version |
|---|---|---|
| [Python](https://www.python.org/downloads/) | Core language | 3.11+ |
| [FastAPI](https://fastapi.tiangolo.com/) | REST API framework | 0.110+ |
| [PostgreSQL](https://www.postgresql.org/) | Relational database | 14+ |
| [SQLAlchemy](https://docs.sqlalchemy.org/) | ORM and database toolkit | 2.0+ |
| [Apache Kafka](https://kafka.apache.org/) | Event streaming platform | 3.x |
| [kafka-python](https://kafka-python.readthedocs.io/) | Python Kafka client | 2.0+ |
| [Apache Airflow](https://airflow.apache.org/) | Workflow orchestration | 2.9+ |
| [Pydantic](https://docs.pydantic.dev/) | Data validation | 2.0+ |
| [Uvicorn](https://www.uvicorn.org/) | ASGI server | 0.29+ |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client                               │
│              (browser, curl, other services)                │
└─────────────────────┬───────────────────────────────────────┘
                      │  HTTP
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI (port 8000)                       │
│              Auto-generated OpenAPI docs at /docs           │
│    Pydantic models validate all requests and responses      │
└──────────────┬──────────────────────────┬───────────────────┘
               │ SQLAlchemy ORM           │ kafka-python
               ▼                          ▼
┌──────────────────────┐    ┌─────────────────────────────────┐
│  PostgreSQL           │    │  Apache Kafka                   │
│  nwsl_db             │    │  topic: nwsl-players            │
│  table: players      │    │  events: player_added,          │
│                      │    │          player_updated          │
└──────────────────────┘    └─────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│               Apache Airflow (port 8080)                    │
│   DAGs: gotham_fc_roster, denver_summit_roster              │
│   Scheduled workflow orchestration for roster tasks         │
└─────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
nwsl-roster-api/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, all endpoints
│   ├── models.py        # Pydantic request/response models
│   ├── database.py      # SQLAlchemy engine, session, ORM models
│   ├── data.py          # Database query functions
│   ├── seed_data.py     # Gotham FC and Denver Summit rosters
│   └── kafka_client.py  # Kafka producer, event publishing
├── dags/
│   ├── gotham_fc.py     # Airflow DAG — Gotham FC roster workflow
│   └── denver_summit.py # Airflow DAG — Denver Summit roster workflow
├── requirements.txt
└── README.md
```

---

## Prerequisites

### 1. Python 3.11+
Download from [python.org](https://www.python.org/downloads/) or install via your package manager.

```bash
python3 --version  # should be 3.11 or higher
```

### 2. PostgreSQL
**macOS:**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Ubuntu / WSL2:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo service postgresql start
```

**Windows:** Download from [postgresql.org/download/windows](https://www.postgresql.org/download/windows/)

### 3. Apache Kafka
Download from [kafka.apache.org/downloads](https://kafka.apache.org/downloads). Requires Java 11+.

```bash
# check Java
java -version

# start ZooKeeper (terminal 1)
./bin/zookeeper-server-start.sh config/zookeeper.properties

# start Kafka broker (terminal 2)
./bin/kafka-server-start.sh config/server.properties
```

**Windows (Git Bash):**
```bash
./bin/windows/zookeeper-server-start.bat config/zookeeper.properties
./bin/windows/kafka-server-start.bat config/server.properties
```

### 4. Apache Airflow (optional — for DAG orchestration)
See [airflow.apache.org/docs/apache-airflow/stable/installation](https://airflow.apache.org/docs/apache-airflow/stable/installation/index.html). Recommended to run in WSL2 or Linux — not officially supported on Windows.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/nwsl-roster-api.git
cd nwsl-roster-api
```

### 2. Create and activate a virtual environment

```bash
python3.11 -m venv .venv

# Linux / macOS / WSL2
source .venv/bin/activate

# Windows Git Bash
source .venv/Scripts/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
fastapi>=0.110.0
uvicorn>=0.29.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
kafka-python>=2.0.0
pydantic>=2.0.0
```

### 4. Set up PostgreSQL

```bash
# create database and user
sudo -u postgres psql -c "CREATE USER nwsl WITH PASSWORD 'nwsl';"
sudo -u postgres psql -c "CREATE DATABASE nwsl_db OWNER nwsl;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE nwsl_db TO nwsl;"

# verify connection
psql -U nwsl -d nwsl_db -h localhost -c "SELECT version();"
```

### 5. Create the Kafka topic

```bash
# Linux / macOS / WSL2
./bin/kafka-topics.sh --create \
  --topic nwsl-players \
  --bootstrap-server localhost:9092 \
  --partitions 1 \
  --replication-factor 1

# Windows
./bin/windows/kafka-topics.bat --create ^
  --topic nwsl-players ^
  --bootstrap-server localhost:9092 ^
  --partitions 1 ^
  --replication-factor 1
```

### 6. Run the API

```bash
# must be run from the project root, not from inside app/
cd nwsl-roster-api
uvicorn app.main:app --reload
```

On first startup the API seeds the PostgreSQL database with both team rosters automatically.

---

## API Reference

Interactive documentation is available at **http://localhost:8000/docs** once the server is running.

### Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/teams` | List all teams |
| `GET` | `/teams/{team_name}` | Full roster for a team |
| `GET` | `/teams/{team_name}/players` | Filtered player list |
| `GET` | `/players/{name}` | Single player by name |
| `POST` | `/players` | Add a player (publishes Kafka event) |
| `PUT` | `/players/{name}` | Update a player (publishes Kafka event) |
| `GET` | `/stats/{team_name}` | Squad statistics |

### Query Parameters — `GET /teams/{team_name}/players`

| Parameter | Type | Example |
|---|---|---|
| `position` | string | `?position=Forward` |
| `country` | string | `?country=USA` |
| `min_age` | integer | `?min_age=25` |
| `max_age` | integer | `?max_age=30` |

### Example Requests

```bash
# list all teams
curl http://localhost:8000/teams

# get Gotham FC roster
curl http://localhost:8000/teams/gotham-fc

# get Denver Summit forwards only
curl "http://localhost:8000/teams/denver-summit/players?position=Forward"

# get USA players aged 25-30
curl "http://localhost:8000/teams/gotham-fc/players?country=USA&min_age=25&max_age=30"

# get a single player
curl "http://localhost:8000/players/Rose%20Lavelle"

# add a new player
curl -X POST http://localhost:8000/players \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alex Morgan",
    "number": 13,
    "age": 34,
    "country": "USA",
    "position": "Forward",
    "team": "gotham-fc"
  }'

# update a player
curl -X PUT "http://localhost:8000/players/Alex%20Morgan" \
  -H "Content-Type: application/json" \
  -d '{"note": "Returning from international duty"}'

# squad stats
curl http://localhost:8000/stats/denver-summit
```

### Example Response — `GET /stats/gotham-fc`

```json
{
  "team": "gotham-fc",
  "total_players": 19,
  "average_age": 26.4,
  "countries": ["Brazil", "England", "Germany", "Israel", "USA"],
  "oldest_player": "Katie Stengel",
  "youngest_player": "Jaedyn Shaw",
  "positions": {
    "Goalkeeper": 4,
    "Defender": 7,
    "Midfielder": 5,
    "Forward": 3
  }
}
```

---

## Kafka Events

When a player is added or updated via the API, an event is published to the `nwsl-players` Kafka topic.

**Event types:** `player_added`, `player_updated`

**Message format:**
```json
{
  "name": "Rose Lavelle",
  "number": 16,
  "age": 29,
  "country": "USA",
  "position": "Midfielder",
  "team": "gotham-fc",
  "note": null
}
```

**Consume events:**
```bash
# Linux / macOS / WSL2
./bin/kafka-console-consumer.sh \
  --topic nwsl-players \
  --from-beginning \
  --bootstrap-server localhost:9092
```

---

## Airflow DAGs

Two DAGs are included for workflow orchestration of roster tasks.

### Setup

```bash
export AIRFLOW_HOME=~/airflow
airflow db migrate
airflow users create \
  --username admin --password admin \
  --firstname Admin --lastname Admin \
  --role Admin --email your@email.com

# copy DAGs
cp dags/*.py ~/airflow/dags/

# start services
airflow webserver --port 8080 &
airflow scheduler &
```

Open **http://localhost:8080** and trigger DAGs manually from the UI.

### DAG: `gotham_fc_roster`

```
print_squad_header >> print_roster
```

Prints the NJ/NY Gotham FC squad header and full roster by position.

### DAG: `denver_summit_roster`

```
print_squad_header >> print_roster >> print_squad_stats
```

Prints the Denver Summit roster and calculates squad statistics including average age and countries represented.

---

## Database Schema

```sql
CREATE TABLE players (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR NOT NULL,
    number      INTEGER,
    age         INTEGER,
    country     VARCHAR NOT NULL,
    position    VARCHAR NOT NULL,
    team        VARCHAR NOT NULL,
    note        TEXT
);

CREATE INDEX ix_players_team ON players (team);
```

Verify data after seeding:
```bash
psql -U nwsl -d nwsl_db -h localhost \
  -c "SELECT name, position, team FROM players ORDER BY team, position LIMIT 10;"
```

---

## Teams

### NJ/NY Gotham FC
New Jersey/New York NWSL team — 19 players from 5 countries including Germany, Brazil, England, Israel, and the USA.

### Denver Summit FC
Denver's NWSL team — 27 players from 8 countries including France, Canada, Mexico, Germany, England, Spain, Japan, and the USA.

---

## Learning Notes

This project was built to demonstrate hands-on experience with a modern Python backend stack:

- **FastAPI** — async REST API with automatic OpenAPI documentation, Pydantic validation, and dependency injection
- **PostgreSQL + SQLAlchemy** — relational database with ORM, session management, and database seeding
- **Apache Kafka** — event publishing on data mutations using a singleton producer pattern
- **Apache Airflow** — DAG-based workflow orchestration with `PythonOperator` and task dependencies
- **Defensive coding** — graceful Kafka failure handling, None-safe deserializers, proper HTTP status codes

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [kafka-python Documentation](https://kafka-python.readthedocs.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
