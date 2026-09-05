from fastapi import FastAPI

from supportflow_ai.api.dependencies.tickets import get_ticket_repository
from supportflow_ai.api.routes.health import router as health_router
from supportflow_ai.api.routes.tickets import router as ticket_router
from supportflow_ai.repositories.ticket import TicketRepository


def create_app(ticket_repository: TicketRepository | None = None) -> FastAPI:
    app = FastAPI(title="SupportFlow AI", version="0.1.0")
    if ticket_repository is not None:
        app.dependency_overrides[get_ticket_repository] = lambda: ticket_repository
    app.include_router(health_router)
    app.include_router(ticket_router)
    return app


app = create_app()
