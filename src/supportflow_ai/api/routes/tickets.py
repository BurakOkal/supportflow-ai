from typing import Annotated, NoReturn
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response, status

from supportflow_ai.api.dependencies.tickets import TicketServiceDependency
from supportflow_ai.domain.ticket import Ticket
from supportflow_ai.schemas.ticket import (
    TicketCreate,
    TicketListResponse,
    TicketResponse,
    TicketUpdate,
)
from supportflow_ai.services.ticket import TicketNotFoundError

router = APIRouter(prefix="/api/v1/tickets", tags=["tickets"])


def _raise_not_found(error: TicketNotFoundError) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(error),
    ) from error


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: TicketCreate,
    service: TicketServiceDependency,
) -> Ticket:
    return service.create_ticket(
        subject=payload.subject,
        description=payload.description,
        customer_email=str(payload.customer_email),
    )


@router.get("", response_model=TicketListResponse)
def list_tickets(
    service: TicketServiceDependency,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> TicketListResponse:
    tickets, total = service.list_tickets(offset, limit)
    return TicketListResponse(
        items=[TicketResponse.model_validate(ticket) for ticket in tickets],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: UUID, service: TicketServiceDependency) -> Ticket:
    try:
        return service.get_ticket(ticket_id)
    except TicketNotFoundError as error:
        _raise_not_found(error)


@router.patch("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: UUID,
    payload: TicketUpdate,
    service: TicketServiceDependency,
) -> Ticket:
    try:
        return service.update_ticket(
            ticket_id,
            subject=payload.subject,
            description=payload.description,
            status=payload.status,
        )
    except TicketNotFoundError as error:
        _raise_not_found(error)


@router.delete(
    "/{ticket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_ticket(ticket_id: UUID, service: TicketServiceDependency) -> Response:
    try:
        service.delete_ticket(ticket_id)
    except TicketNotFoundError as error:
        _raise_not_found(error)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
