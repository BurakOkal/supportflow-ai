from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, event, inspect, text
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import CreateSchema, DropSchema

from supportflow_ai.config import get_settings
from supportflow_ai.db.base import Base
from supportflow_ai.db.session import get_session
from supportflow_ai.domain.ticket import Ticket, TicketCategory, TicketPriority, TicketStatus
from supportflow_ai.main import create_app
from supportflow_ai.repositories.sqlalchemy_ticket import SQLAlchemyTicketRepository

pytestmark = pytest.mark.postgres
ROOT = Path(__file__).resolve().parents[1]


def migration_config() -> Config:
    return Config(str(ROOT / "alembic.ini"))


@pytest.fixture
def postgres_engine() -> Iterator[Engine]:
    schema = f"test_supportflow_{uuid4().hex}"
    admin = create_engine(
        get_settings().database_url,
        hide_parameters=True,
        connect_args={"connect_timeout": 5},
    )
    engine = None
    created = False
    try:
        with admin.begin() as connection:
            connection.execute(CreateSchema(schema))
        created = True
        engine = create_engine(
            get_settings().database_url,
            hide_parameters=True,
            connect_args={"connect_timeout": 5, "options": f"-csearch_path={schema}"},
        )
        with engine.begin() as connection:
            config = migration_config()
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
        yield engine
    finally:
        if engine is not None:
            engine.dispose()
        if created:
            with admin.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True))
        admin.dispose()


@pytest.fixture
def ticket() -> Ticket:
    now = datetime.now(UTC)
    return Ticket(
        id=uuid4(),
        subject="Payment was charged twice",
        description="The same invoice was charged to my card twice.",
        customer_email="customer@example.com",
        status=TicketStatus.OPEN,
        category=TicketCategory.UNCLASSIFIED,
        priority=TicketPriority.UNASSIGNED,
        created_at=now,
        updated_at=now,
    )


def test_crud_persists_across_sessions(postgres_engine, ticket):
    factory = sessionmaker(postgres_engine)
    with factory() as session:
        SQLAlchemyTicketRepository(session).add(ticket)

    with factory() as session:
        repository = SQLAlchemyTicketRepository(session)
        loaded = repository.get_by_id(ticket.id)
        assert loaded == ticket
        assert isinstance(loaded, Ticket)
        assert isinstance(loaded.id, UUID)
        assert loaded.status is TicketStatus.OPEN
        assert loaded.created_at.utcoffset() == timedelta(0)
        updated = replace(
            loaded,
            subject="Updated payment issue",
            description="The customer confirmed that the issue is now resolved.",
            status=TicketStatus.RESOLVED,
            category=TicketCategory.BILLING,
            priority=TicketPriority.HIGH,
            updated_at=ticket.updated_at + timedelta(seconds=1),
        )
        repository.update(updated)

    with factory() as session:
        repository = SQLAlchemyTicketRepository(session)
        assert repository.get_by_id(ticket.id) == updated
        assert repository.get_by_id(uuid4()) is None
        assert repository.delete(ticket.id) is True

    with factory() as session:
        repository = SQLAlchemyTicketRepository(session)
        assert repository.get_by_id(ticket.id) is None
        assert repository.delete(ticket.id) is False
        assert repository.list_tickets(0, 20) == ([], 0)


def test_pagination_uses_sql_and_keeps_total_for_empty_pages(postgres_engine, ticket):
    # A timestamp tie must still produce deterministic pages using the UUID.
    tickets = [replace(ticket, id=UUID(int=i + 1)) for i in range(3)]
    with Session(postgres_engine) as session:
        repository = SQLAlchemyTicketRepository(session)
        for item in reversed(tickets):
            repository.add(item)

    statements = []

    def capture_sql(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement.upper())

    event.listen(postgres_engine, "before_cursor_execute", capture_sql)
    try:
        with Session(postgres_engine) as session:
            repository = SQLAlchemyTicketRepository(session)
            assert repository.list_tickets(1, 1) == ([tickets[1]], 3)
            assert repository.list_tickets(10, 1) == ([], 3)
    finally:
        event.remove(postgres_engine, "before_cursor_execute", capture_sql)

    assert any("COUNT(" in sql for sql in statements)
    assert any("LIMIT" in sql and "OFFSET" in sql and "ORDER BY" in sql for sql in statements)


@pytest.mark.parametrize("operation", ["add", "update", "delete"])
def test_failed_write_rolls_back_and_session_can_be_reused(
    postgres_engine, ticket, operation,
):
    with Session(postgres_engine) as session:
        repository = SQLAlchemyTicketRepository(session)
        repository.add(ticket)
        if operation == "add":
            with pytest.raises(IntegrityError):
                repository.add(ticket)
        elif operation == "update":
            with pytest.raises(DataError):
                repository.update(replace(ticket, subject="x" * 201))
        else:
            # Reject DELETE in PostgreSQL to exercise rollback after execute fails.
            with postgres_engine.begin() as connection:
                connection.execute(text("""
                    CREATE FUNCTION reject_ticket_delete() RETURNS trigger
                    LANGUAGE plpgsql AS $$ BEGIN
                        RAISE EXCEPTION 'test delete rejected' USING ERRCODE = '23514';
                    END $$
                """))
                connection.execute(text("""
                    CREATE TRIGGER reject_ticket_delete BEFORE DELETE ON tickets
                    FOR EACH ROW EXECUTE FUNCTION reject_ticket_delete()
                """))
            with pytest.raises(IntegrityError):
                repository.delete(ticket.id)

        assert repository.get_by_id(ticket.id) == ticket
        another = replace(ticket, id=uuid4())
        repository.add(another)

    with Session(postgres_engine) as session:
        assert SQLAlchemyTicketRepository(session).get_by_id(another.id) == another


def test_migration_matches_metadata_and_can_downgrade_and_upgrade(postgres_engine):
    with postgres_engine.begin() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        assert context.get_current_revision() == "0001_create_tickets"
        assert compare_metadata(context, Base.metadata) == []
        inspector = inspect(connection)
        checks = {constraint["name"] for constraint in inspector.get_check_constraints("tickets")}
        assert checks == {
            "ck_tickets_ticket_status", "ck_tickets_ticket_category", "ck_tickets_ticket_priority",
        }
        config = migration_config()
        config.attributes["connection"] = connection
        command.downgrade(config, "base")
        assert not inspect(connection).has_table("tickets")
        command.upgrade(config, "head")
        assert inspect(connection).has_table("tickets")


def test_api_data_survives_app_recreation(postgres_engine):
    factory = sessionmaker(postgres_engine, expire_on_commit=False)

    def session_dependency():
        with factory() as session:
            yield session

    def new_app():
        app = create_app()
        app.dependency_overrides[get_session] = session_dependency
        return app

    with TestClient(new_app()) as client:
        response = client.post("/api/v1/tickets", json={
            "subject": "Persistent ticket",
            "description": "This ticket should survive a new application instance.",
            "customer_email": "customer@example.com",
        })
        assert response.status_code == 201
        created = response.json()

    with TestClient(new_app()) as client:
        ticket_path = f"/api/v1/tickets/{created['id']}"
        assert client.get(ticket_path).json() == created
        assert client.get("/api/v1/tickets").json() == {
            "items": [created], "total": 1, "offset": 0, "limit": 20,
        }
        response = client.patch(ticket_path, json={"status": "closed"})
        assert response.status_code == 200
        updated = response.json()
        assert updated["status"] == "closed"
        assert updated["created_at"] == created["created_at"]
        assert updated["updated_at"] != created["updated_at"]

    with TestClient(new_app()) as client:
        assert client.get(ticket_path).json() == updated
        response = client.delete(ticket_path)
        assert response.status_code == 204
        assert response.content == b""
        assert client.get(ticket_path).status_code == 404
        assert client.patch(ticket_path, json={"status": "open"}).status_code == 404
        assert client.delete(ticket_path).status_code == 404
