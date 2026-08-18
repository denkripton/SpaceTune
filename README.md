# SpaceTune

## 🎵 Music Streaming Backend

SpaceTune is a music streaming backend platform, built as a sequential, production-grade FastAPI service.
It allows users to upload, stream, grade, and manage tracks

## ✨ Features

* 🔐 JWT-based authentication (access + refresh tokens)
* 🌐 Google OAuth 2.0 login
* 🎶 Track upload, retrieval, and grading
* ☁️ AWS S3 integration for audio/image storage
* 🩺 Health-check endpoint (`GET /health`) with DB connectivity probe
* 📝 Structured JSON logging with automatic sensitive-field redaction
* 🔗 Correlation-ID propagation across requests (`X-Request-ID`)
* 🐳 Multi-stage, non-root Docker image + Docker Compose orchestration

(Telegram bot and frontend are planned for later stages — see Roadmap below)

## 🛠 Tech Stack

**Backend**

* Python 3.13
* FastAPI
* PostgreSQL + SQLAlchemy (async) + Alembic
* Redis *(planned)*
* AWS S3 (boto3)
* JWT (PyJWT), bcrypt
* structlog (structured JSON logging)

**Infrastructure**

* Docker / Docker Compose (multi-stage build, non-root `appuser`)

**Package management**

* [uv](https://github.com/astral-sh/uv)

## 🚀 Launch

### 1. Clone the repository

Make sure you have [git](https://git-scm.com/downloads) installed.

```bash
git clone {repository url}
cd SpaceTune
```

The `compose.yml` files live at the repository root — all commands below are run from `SpaceTune/`, not from `SpaceTune/backend/`.

### 2. Environment variables setup

Two `.env` files are required — one at the repo root, one inside `backend/`:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

**Root `.env`** — `DB_USER`, `DB_PASSWORD`, `DB_NAME` (used by Docker Compose to provision the `db` service).

**`backend/.env`** — app secrets: `JWT_SECRET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_REDIRECT_URI`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_USERINFO_URL`, `AWS_SECRET`, `AWS_ACCESS`, `AWS_REGION`, `BUCKET_NAME`.

### 3. Run with Docker Compose (recommended)

Make sure you have [Docker](https://docs.docker.com/get-docker/) and Docker Compose installed.

```bash
docker compose -f compose.yml -f compose.dev.yml up --build
```

This starts the backend (hot-reload enabled, port `8000`) and a PostgreSQL 16 instance together. The backend waits for the database to report healthy (`depends_on: condition: service_healthy`) before starting. Database migrations still need to be applied — see step 5.

### 4. (Alternative) Local setup without Docker

Install [uv](https://github.com/astral-sh/uv) and a [Python interpreter](https://www.python.org/downloads/).

```bash
cd backend
uv venv
```

Activate the environment:

* Windows:

```bash
.venv\Scripts\activate
```

* Linux/macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
uv sync --frozen
```

This requires a PostgreSQL instance reachable at the `DB_URL` you set in `backend/.env` (e.g. run only the `db` service via `docker compose up db`).

### 5. Database migrations

From `backend/`, apply all migrations to create the schema:

```bash
uv run alembic upgrade head
```

If running inside the Docker container, exec into it instead:

```bash
docker compose exec backend alembic upgrade head
```

### 6. Run the backend (local only — Docker Compose runs this automatically)

```bash
uv run uvicorn src.api:api.app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 7. Health check

Verify the service and database connection are up:

```bash
curl http://localhost:8000/health
```

Returns `200` when the database is reachable, or `503` if it isn't.

### 8. Running tests

From `backend/`:

```bash
uv run pytest
```

Some integration tests require a real PostgreSQL connection and are skipped automatically if one isn't available in the environment.