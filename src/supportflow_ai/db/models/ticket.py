from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from supportflow_ai.db.base import Base
from supportflow_ai.domain.ticket import TicketCategory, TicketPriority, TicketStatus


class TicketModel(Base):
    __tablename__ = "tickets"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    subject: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    customer_email: Mapped[str] = mapped_column(String(320), index=True)
    status: Mapped[TicketStatus] = mapped_column(
        Enum(
            TicketStatus,
            name="ticket_status",
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        )
    )
    category: Mapped[TicketCategory] = mapped_column(
        Enum(
            TicketCategory,
            name="ticket_category",
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        )
    )
    priority: Mapped[TicketPriority] = mapped_column(
        Enum(
            TicketPriority,
            name="ticket_priority",
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        )
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
