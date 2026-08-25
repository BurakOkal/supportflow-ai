from abc import ABC, abstractmethod
from uuid import UUID

from supportflow_ai.domain.ticket import Ticket


class TicketRepository(ABC):
    @abstractmethod
    def add(self, ticket: Ticket) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, ticket_id: UUID) -> Ticket | None:
        raise NotImplementedError

    @abstractmethod
    def list_tickets(self, offset: int, limit: int) -> tuple[list[Ticket], int]:
        raise NotImplementedError

    @abstractmethod
    def update(self, ticket: Ticket) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, ticket_id: UUID) -> bool:
        raise NotImplementedError


class InMemoryTicketRepository(TicketRepository):
    def __init__(self) -> None:
        self._tickets: dict[UUID, Ticket] = {}

    def add(self, ticket: Ticket) -> None:
        self._tickets[ticket.id] = ticket

    def get_by_id(self, ticket_id: UUID) -> Ticket | None:
        return self._tickets.get(ticket_id)

    def list_tickets(self, offset: int, limit: int) -> tuple[list[Ticket], int]:
        tickets = list(self._tickets.values())
        return tickets[offset : offset + limit], len(tickets)

    def update(self, ticket: Ticket) -> None:
        self._tickets[ticket.id] = ticket

    def delete(self, ticket_id: UUID) -> bool:
        return self._tickets.pop(ticket_id, None) is not None
