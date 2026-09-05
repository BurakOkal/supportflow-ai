from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from supportflow_ai.db.session import get_session
from supportflow_ai.repositories.sqlalchemy_ticket import SQLAlchemyTicketRepository
from supportflow_ai.repositories.ticket import TicketRepository
from supportflow_ai.services.ticket import TicketService


def get_ticket_repository(
    session: Annotated[Session, Depends(get_session)],
) -> TicketRepository:
    return SQLAlchemyTicketRepository(session)


def get_ticket_service(
    repository: Annotated[TicketRepository, Depends(get_ticket_repository)],
) -> TicketService:
    return TicketService(repository)


TicketServiceDependency = Annotated[TicketService, Depends(get_ticket_service)]
