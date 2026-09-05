from collections.abc import Iterator
from contextlib import contextmanager
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from supportflow_ai.db.models import TicketModel
from supportflow_ai.domain.ticket import Ticket
from supportflow_ai.repositories.ticket import TicketRepository


def _to_model(ticket: Ticket) -> TicketModel:
    return TicketModel(
        id=ticket.id,
        subject=ticket.subject,
        description=ticket.description,
        customer_email=ticket.customer_email,
        status=ticket.status,
        category=ticket.category,
        priority=ticket.priority,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )


def _to_domain(model: TicketModel) -> Ticket:
    return Ticket(
        id=model.id,
        subject=model.subject,
        description=model.description,
        customer_email=model.customer_email,
        status=model.status,
        category=model.category,
        priority=model.priority,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SQLAlchemyTicketRepository(TicketRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    @contextmanager
    def _write(self) -> Iterator[None]:
        # A preceding read may already have started the session's transaction.
        try:
            yield
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise

    def add(self, ticket: Ticket) -> None:
        with self._write():
            self._session.add(_to_model(ticket))

    def get_by_id(self, ticket_id: UUID) -> Ticket | None:
        model = self._session.get(TicketModel, ticket_id)
        return _to_domain(model) if model is not None else None

    def list_tickets(self, offset: int, limit: int) -> tuple[list[Ticket], int]:
        total = self._session.scalar(select(func.count()).select_from(TicketModel))
        statement = (
            select(TicketModel)
            .order_by(TicketModel.created_at, TicketModel.id)
            .offset(offset)
            .limit(limit)
        )
        tickets = [_to_domain(model) for model in self._session.scalars(statement)]
        return tickets, total or 0

    def update(self, ticket: Ticket) -> None:
        with self._write():
            self._session.merge(_to_model(ticket))

    def delete(self, ticket_id: UUID) -> bool:
        with self._write():
            deleted_id = self._session.scalar(
                delete(TicketModel)
                .where(TicketModel.id == ticket_id)
                .returning(TicketModel.id)
            )
        return deleted_id is not None
