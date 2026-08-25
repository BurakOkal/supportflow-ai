# SupportFlow AI

SupportFlow AI is a FastAPI service for managing customer support tickets.

## Development setup

```console
uv sync --dev
```

## Run the API

```console
uv run fastapi dev src/supportflow_ai/main.py
```

## Run tests

```console
uv run pytest
```

## Endpoints

- `GET /health`
- `POST /api/v1/tickets`
- `GET /api/v1/tickets`
- `GET /api/v1/tickets/{ticket_id}`
- `PATCH /api/v1/tickets/{ticket_id}`
- `DELETE /api/v1/tickets/{ticket_id}`

Ticket data is currently stored only in memory and is reset when the application restarts.
