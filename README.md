# SupportFlow AI

SupportFlow AI is a FastAPI service for managing customer support tickets.

## Development setup

```console
uv sync --dev
```

## PostgreSQL

Copy `.env.example` to `.env` if you do not already have one (PowerShell):

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Set `POSTGRES_PASSWORD` in `.env` before the first database start. Configuration
is loaded centrally with Pydantic Settings; environment variables override `.env`.
Keep `.env` private and out of Git. The API runs on the host and connects to
`POSTGRES_HOST` and `POSTGRES_PORT` (by default `localhost:5432`).

```console
docker compose config --quiet
docker compose up -d --wait db
docker compose ps
uv run alembic upgrade head
uv run alembic current
```

Database tables are managed only through Alembic migrations. The application
does not create tables on startup. Apply migrations before using ticket endpoints.
To add a schema change, update the ORM model, generate a migration with
`uv run alembic revision --autogenerate -m "describe change"`, review it, and run
`uv run alembic upgrade head`.

PostgreSQL data survives API and container restarts in the `postgres_data` Docker
volume. `docker compose stop db` stops the database without deleting its data.
**`docker compose down -v` deletes the volume and all stored database data.**
Changing the credentials in `.env` does not update users in an existing database
volume; keep the configuration consistent with the existing database credentials.

## Run the API

```console
uv run fastapi dev src/supportflow_ai/main.py
```

Open `http://127.0.0.1:8000/docs` for the interactive API. Stop the server with
`Ctrl+C` when finished.

## Run tests

```console
uv run pytest
```

The default test suite requires neither PostgreSQL nor `.env`. API unit tests
explicitly inject a fresh `InMemoryTicketRepository` for each test.

To also run PostgreSQL persistence and migration tests against the configured
database after starting it:

```console
uv run pytest --postgres
```

PostgreSQL tests create and remove their own randomly named schema using the
configured database user, which must have permission to create schemas. They
apply Alembic migrations there and leave application tables and data untouched.

## Endpoints

- `GET /health`
- `POST /api/v1/tickets`
- `GET /api/v1/tickets`
- `GET /api/v1/tickets/{ticket_id}`
- `PATCH /api/v1/tickets/{ticket_id}`
- `DELETE /api/v1/tickets/{ticket_id}`

The normal dependency flow is router -> `TicketService` ->
`SQLAlchemyTicketRepository` -> PostgreSQL, using synchronous SQLAlchemy 2.x and
psycopg 3. Each ticket request gets its own Session, which is closed after the
request. Engine and session factory initialization is lazy; importing the app or
calling `/health` does not require a database connection. Writes commit before
returning a successful response and roll back on failure.
