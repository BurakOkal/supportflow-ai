from fastapi import FastAPI

from supportflow_ai.api.routes.health import router as health_router
from supportflow_ai.api.routes.tickets import router as ticket_router
from supportflow_ai.repositories.ticket import (
    InMemoryTicketRepository,
    TicketRepository,
)


def create_app(ticket_repository: TicketRepository | None = None) -> FastAPI:
    app = FastAPI(title="SupportFlow AI", version="0.1.0")
    app.state.ticket_repository = (
        ticket_repository
        if ticket_repository is not None
        else InMemoryTicketRepository()
    )
    app.include_router(health_router)
    app.include_router(ticket_router)
    return app


app = create_app()
