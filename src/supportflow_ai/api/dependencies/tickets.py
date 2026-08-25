from typing import Annotated, cast

from fastapi import Depends, Request

from supportflow_ai.repositories.ticket import TicketRepository
from supportflow_ai.services.ticket import TicketService


def get_ticket_repository(request: Request) -> TicketRepository:
    return cast(TicketRepository, request.app.state.ticket_repository)


def get_ticket_service(
    repository: Annotated[TicketRepository, Depends(get_ticket_repository)],
) -> TicketService:
    return TicketService(repository)


TicketServiceDependency = Annotated[TicketService, Depends(get_ticket_service)]
