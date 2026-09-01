# Quantom

Async quantum-circuit execution platform built with **FastAPI**, **FastStream**, **Redis Streams**, **PostgreSQL**, and **Qiskit Aer**.

Submit an OpenQASM 3 circuit via the REST API → the circuit is queued onto a Redis stream → a worker picks it up, simulates it with Qiskit Aer, and writes the measurement counts back to Postgres → poll the API for the result.

***

## Quick Start

```bash
docker compose up --build
```

This single command builds both application images and starts **all five services** (API, worker, Redis, RedisInsight, PostgreSQL).\
The API is available at [**http://localhost:8000**](http://localhost:8000) once everything is healthy.

To rebuild after code changes, always pass `--build`:

```
docker compose up --build
```

***

## Project Structure

```
quantom/
├── docker-compose.yml
├── pyproject.toml
├── src/
│   ├── common/
│   │   ├── settings.py          # Environment variables configuration
│   │   ├── models/              # Pydantic + SQLModel data models
│   │   │   ├── task_status.py   # TaskStatus enum
│   │   │   ├── task_record.py   # TaskRecord SQLModel (DB table)
│   │   │   └── task_message.py  # TaskMessage schema (broker payload)
│   │   ├── task_store.py        # Async PostgreSQL CRUD for tasks
│   │   └── tasks_broker.py      # Redis Streams broker & publisher
│   │
│   ├── quantum_api/             # REST API service
│   │   ├── Dockerfile
│   │   ├── main.py              # ← Entrypoint (FastAPI app)
│   │   ├── data_models/         # Request / response schemas
│   │   │   └── tasks.py
│   │   └── api/
│   │       ├── tasks.py         # POST /tasks  &  GET /tasks/{id}
│   │       └── tests/           # Contract tests for task endpoints
│   │           ├── conftest.py
│   │           └── test_tasks.py
│   │
│   └── quantum_service/         # Background worker service
│       ├── Dockerfile
│       ├── main.py              # ← Entrypoint (FastStream app)
│       └── core.py              # Qiskit Aer circuit execution + retry logic
│
└── integration_tests/
    └── test_integration.py      # End-to-end tests (marked @integration)
```

***

## Services & Entrypoints

### quantum\_api — REST API

|                |                                                                         |
| -------------- | ----------------------------------------------------------------------- |
| **Framework**  | FastAPI                                                                 |
| **Entrypoint** | `src/quantum_api/main.py` → `app = FastAPI()`                           |
| **Docker CMD** | `uv run fastapi run src/quantum_api/main.py --host 0.0.0.0 --port 8000` |
| **Port**       | `8000`                                                                  |

On startup, the API creates the database tables (if missing) and connects to the Redis broker.

**Endpoints:**

| Method | Path               | Description                                                                              |
| ------ | ------------------ | ---------------------------------------------------------------------------------------- |
| `POST` | `/tasks`           | Submit an OpenQASM 3 circuit (`{"qc": "..."}`) — returns `202 Accepted` with a `task_id` |
| `GET`  | `/tasks/{task_id}` | Poll task status — returns `pending`, `completed` (with measurement counts), or `404`    |

***

### quantum\_service — Background Worker

|                |                                                            |
| -------------- | ---------------------------------------------------------- |
| **Framework**  | FastStream (Redis Streams)                                 |
| **Entrypoint** | `src/quantum_service/main.py` → `app = FastStream(broker)` |
| **Docker CMD** | `uv run faststream run src.quantum_service.main:app`       |
| **Stream**     | `tasks` (consumer group: `task-workers`)                   |

The worker subscribes to the `tasks` Redis stream, simulates each circuit using **Qiskit Aer** (1024 shots), and writes measurement counts back to Postgres.\
Failed executions are retried with exponential back-off (configurable via `MAX_RETRIES`).

***

### Infrastructure

| Service          | Image                       | Port   |
| ---------------- | --------------------------- | ------ |
| **PostgreSQL**   | `postgres:16-alpine`        | `5432` |
| **Redis**        | `redis:7-alpine`            | `6379` |
| **RedisInsight** | `redis/redisinsight:latest` | `5540` |

***

## Environment Variables

All application settings are loaded from environment variables with sensible defaults for local development.

### Application Settings

| Variable       | Used by     | Default                                                         | Description                                                                                 |
| -------------- | ----------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `DATABASE_URL` | API, Worker | `postgresql+asyncpg://postgres:postgres@localhost:5432/quantom` | Async SQLAlchemy connection string for PostgreSQL                                           |
| `REDIS_URL`    | API, Worker | `redis://localhost:6379`                                        | Redis connection URL (used by FastStream broker)                                            |
| `HOSTNAME`     | Worker      | random UUID                                                     | Consumer ID for the Redis Streams consumer group — defaults to container hostname in Docker |
| `MAX_RETRIES`  | Worker      | `5`                                                             | Maximum retry attempts for circuit simulation failures (`MemoryError`, `AerError`)          |

***

## Usage Example

```bash
docker compose up
```

Use `--build` flag when making changes to the code or running for the first time.

```bash
docker compose up --build
```

***

## Running Tests

```bash
# Unit tests (default)
uv run pytest

# Integration tests (requires running services)
docker compose up --build -d
uv run pytest -m integration
```
