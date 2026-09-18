# pipeline_youtube

An ELT (Extract, Load, Transform) pipeline that pulls video-level statistics for a YouTube channel via the **YouTube Data API v3**, stages the raw data in **PostgreSQL**, cleans and enriches it, and loads it into a queryable "core" table. Orchestrated end-to-end with **Apache Airflow** (CeleryExecutor) and containerized with **Docker Compose**.

## How it works

The pipeline is split into two Airflow DAGs that hand off to each other:

### 1. `extraction_DAG` (runs hourly)
1. **`get_creator_playlist`** — resolves the target channel's "uploads" playlist ID via the YouTube Data API.
2. **`get_playlist_details_and_videos`** — pages through the uploads playlist and fetches `contentDetails`, `statistics`, and `snippet` for every video (title, published date, duration, views, likes, comments).
3. **`save_data_to_json`** — writes the collected video records to a timestamped JSON file under `data/`.
4. **`trigger_load_dag`** — triggers `load_transform_data_DAG`.

### 2. `load_transform_data_DAG`
1. **`make_staging_table`** — creates a `videos_staging` table (raw, text-typed columns) if it doesn't exist.
2. **`load_data_to_staging`** — upserts the extracted records into staging (`ON CONFLICT` on `videoId`).
3. **`load_staged_data`** — reads the staging table back out.
4. **`transform_staged_data`** — cleans the data: converts ISO 8601 durations (`PT#H#M#S`) to seconds, parses timestamps, casts view/like/comment counts to integers, and drops invalid rows.
5. **`calculate_basic_stats`** — derives `percentageOfLiking` and `percentageOfComenting` (likes/comments as a % of views).
6. **`make_core_id`** — creates the `videos_core` table (properly typed) if it doesn't exist.
7. **`load_data_to_core_table`** — upserts the transformed data into `videos_core` and removes any videos no longer present upstream.

## Architecture

| Component | Role |
|---|---|
| **Airflow webserver / scheduler / worker** | Orchestrates and executes the DAGs (CeleryExecutor) |
| **Redis** | Celery message broker between the scheduler and workers |
| **PostgreSQL** | Hosts three separate databases: Airflow metadata, Celery result backend, and the pipeline's own ELT data (`youtube_elt`) |
| **YouTube Data API v3** | Source of video metadata and statistics |

On first boot, `docker/postgres/init-multiple-databases.sh` provisions all three Postgres databases and their dedicated users from environment variables.

## Project structure

```
.
├── dags/
│   ├── extraction_DAG.py          # Hourly extraction from the YouTube API
│   └── transformation_DAG.py      # Staging → transform → core load
├── include/
│   ├── extract.py                 # YouTube API calls
│   ├── load.py                    # Postgres staging/core table logic
│   └── transform.py                # Data cleaning & stats
├── docker/
│   └── postgres/
│       └── init-multiple-databases.sh
├── Dockerfile                      # Custom Airflow image (adds requirements.txt)
├── docker-compose.yaml             # Airflow + Postgres + Redis stack
├── requirements.txt                # Python deps installed into the Airflow image
└── .env.example                    # Template for required environment variables
```

## Prerequisites

- Docker & Docker Compose
- A [YouTube Data API v3](https://console.cloud.google.com/apis/library/youtube.googleapis.com) key
- At least 4 GB RAM / 2 CPUs / 10 GB free disk available to Docker (Airflow's own recommendation)

## Setup

1. **Clone the repo and copy the environment template:**
   ```bash
   git clone https://github.com/Aymanemjj/pipeline_youtube.git
   cd pipeline_youtube
   cp .env.example .env
   ```

2. **Fill in `.env`**, in particular:
   - `FERNET_KEY` — generate one with:
     ```bash
     python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
     ```
   - `AIRFLOW_WWW_USER_USERNAME` / `AIRFLOW_WWW_USER_PASSWORD` — Airflow UI login
   - `API_KEY` — your YouTube Data API v3 key
   - `CHANNEL_HANDLE` — target channel's handle (no `@`)
   - Postgres credentials for the metadata, Celery, and ELT databases
   - `AIRFLOW_UID` — on Linux, run `id -u` and use that value (defaults to `50000`)

3. **Build and start the stack:**
   ```bash
   docker compose up -d --build
   ```
   The `airflow-init` service provisions the metadata DB and admin user before the webserver, scheduler, and worker come up.

4. **Open the Airflow UI** at [http://localhost:8080](http://localhost:8080) and log in with the credentials from `.env`.

5. **Unpause `extraction_DAG`** — it runs hourly and will trigger `load_transform_data_DAG` automatically after each successful extraction. You can also trigger either DAG manually from the UI.

## Data model

**`videos_staging`** — raw, text-typed mirror of the API response (upserted every run).

**`videos_core`** — cleaned, typed table kept in sync with the source channel:

| Column | Type | Notes |
|---|---|---|
| `videoId` | `TEXT` (PK) | |
| `title` | `TEXT` | |
| `publishedAt` | `TIMESTAMP` | |
| `duration` | `BIGINT` | seconds |
| `viewCount`, `likeCount`, `commentCount` | `BIGINT` | |
| `percentageOfLiking`, `percentageOfComenting` | `INT` | likes/comments as % of views |

Videos removed from the channel are pruned from `videos_core` on each load.

## Notes

- The `postgres` service exposes port `5432` for local inspection/debugging of the ELT database.
- `docker-compose.yaml` and the Postgres `env_file` are wired for local `.env` use — the inline comments flag what to adjust if you move this to CI (e.g. GitHub Actions).