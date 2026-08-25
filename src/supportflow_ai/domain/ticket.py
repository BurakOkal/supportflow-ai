from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class TicketStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketCategory(StrEnum):
    UNCLASSIFIED = "unclassified"
    BILLING = "billing"
    TECHNICAL = "technical"
    ACCOUNT = "account"
    FRAUD = "fraud"
    OTHER = "other"


class TicketPriority(StrEnum):
    UNASSIGNED = "unassigned"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class Ticket:
    id: UUID
    subject: str
    description: str
    customer_email: str
    status: TicketStatus
    category: TicketCategory
    priority: TicketPriority
    created_at: datetime
    updated_at: datetime
