"""Create tickets table.

Revision ID: 0001_create_tickets
Revises:
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_create_tickets"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tickets",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("customer_email", sa.String(length=320), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "open", "in_progress", "resolved", "closed",
                name="ticket_status", native_enum=False, create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "category",
            sa.Enum(
                "unclassified", "billing", "technical", "account", "fraud", "other",
                name="ticket_category", native_enum=False, create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "priority",
            sa.Enum(
                "unassigned", "low", "medium", "high", "critical",
                name="ticket_priority", native_enum=False, create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tickets")),
    )
    op.create_index(op.f("ix_tickets_customer_email"), "tickets", ["customer_email"])


def downgrade() -> None:
    op.drop_index(op.f("ix_tickets_customer_email"), table_name="tickets")
    op.drop_table("tickets")
