from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from supportflow_ai.domain.ticket import (
    TicketCategory,
    TicketPriority,
    TicketStatus,
)

Subject = Annotated[str, Field(min_length=3, max_length=200)]
Description = Annotated[str, Field(min_length=10, max_length=5000)]


class TicketCreate(BaseModel):
    subject: Subject
    description: Description
    customer_email: EmailStr


class TicketUpdate(BaseModel):
    subject: Subject | None = None
    description: Description | None = None
    status: TicketStatus | None = None

    @field_validator("subject", "description", "status", mode="before")
    @classmethod
    def reject_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("field cannot be null")
        return value


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subject: str
    description: str
    customer_email: EmailStr
    status: TicketStatus
    category: TicketCategory
    priority: TicketPriority
    created_at: datetime
    updated_at: datetime


class TicketListResponse(BaseModel):
    items: list[TicketResponse]
    total: int
    offset: int
    limit: int
