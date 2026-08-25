from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from supportflow_ai.domain.ticket import (
    Ticket,
    TicketCategory,
    TicketPriority,
    TicketStatus,
)
from supportflow_ai.repositories.ticket import TicketRepository


class TicketNotFoundError(Exception):
    def __init__(self, ticket_id: UUID) -> None:
        self.ticket_id = ticket_id
        super().__init__(f"Ticket {ticket_id} not found")


class TicketService:
    def __init__(self, repository: TicketRepository) -> None:
        self._repository = repository

    def create_ticket(
        self,
        *,
        subject: str,
        description: str,
        customer_email: str,
    ) -> Ticket:
        now = datetime.now(UTC)
        ticket = Ticket(
            id=uuid4(),
            subject=subject,
            description=description,
            customer_email=customer_email,
            status=TicketStatus.OPEN,
            category=TicketCategory.UNCLASSIFIED,
            priority=TicketPriority.UNASSIGNED,
            created_at=now,
            updated_at=now,
        )
        self._repository.add(ticket)
        return ticket

    def list_tickets(self, offset: int, limit: int) -> tuple[list[Ticket], int]:
        return self._repository.list_tickets(offset, limit)

    def get_ticket(self, ticket_id: UUID) -> Ticket:
        ticket = self._repository.get_by_id(ticket_id)
        if ticket is None:
            raise TicketNotFoundError(ticket_id)
        return ticket

    def update_ticket(
        self,
        ticket_id: UUID,
        *,
        subject: str | None = None,
        description: str | None = None,
        status: TicketStatus | None = None,
    ) -> Ticket:
        ticket = self.get_ticket(ticket_id)
        if subject is None and description is None and status is None:
            return ticket

        updated_ticket = replace(
            ticket,
            subject=subject if subject is not None else ticket.subject,
            description=(
                description if description is not None else ticket.description
            ),
            status=status if status is not None else ticket.status,
            updated_at=datetime.now(UTC),
        )
        self._repository.update(updated_ticket)
        return updated_ticket

    def delete_ticket(self, ticket_id: UUID) -> None:
        if not self._repository.delete(ticket_id):
            raise TicketNotFoundError(ticket_id)
