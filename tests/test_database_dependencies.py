from typing import Annotated

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from supportflow_ai.api.dependencies.tickets import get_ticket_repository
from supportflow_ai.db import session as database
from supportflow_ai.main import create_app
from supportflow_ai.repositories.sqlalchemy_ticket import SQLAlchemyTicketRepository
from supportflow_ai.repositories.ticket import InMemoryTicketRepository, TicketRepository


def test_startup_health_and_in_memory_override_need_no_database(monkeypatch) -> None:
    def unexpected_database_access():
        pytest.fail("Database initialization was not expected")

    monkeypatch.setattr(database, "get_session_factory", unexpected_database_access)
    with TestClient(create_app()) as client:
        assert client.get("/health").json() == {"status": "ok"}
    with TestClient(create_app(InMemoryTicketRepository())) as client:
        assert client.get("/api/v1/tickets").json() == {
            "items": [], "total": 0, "offset": 0, "limit": 20,
        }


@pytest.mark.parametrize("fail_request", [False, True])
def test_default_repository_uses_one_session_per_request_and_closes_it(
    monkeypatch, fail_request: bool,
) -> None:
    sessions = []

    class TrackingSession(Session):
        was_closed = False
        was_rolled_back = False

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            sessions.append(self)

        def close(self):
            self.was_closed = True
            super().close()

        def rollback(self):
            self.was_rolled_back = True
            super().rollback()

    # An unbound session can test dependency lifecycle without connecting anywhere.
    factory = sessionmaker(class_=TrackingSession)
    monkeypatch.setattr(database, "get_session_factory", lambda: factory)
    app = create_app()

    @app.get("/session-probe")
    def session_probe(
        repository: Annotated[TicketRepository, Depends(get_ticket_repository)],
        session: Annotated[Session, Depends(database.get_session)],
    ):
        assert isinstance(repository, SQLAlchemyTicketRepository)
        assert session is sessions[-1]
        if fail_request:
            raise RuntimeError("request failed")
        return {"ok": True}

    with TestClient(app, raise_server_exceptions=False) as client:
        for _ in range(2):
            response = client.get("/session-probe")
            assert response.status_code == (500 if fail_request else 200)
            assert sessions[-1].was_closed
            assert sessions[-1].was_rolled_back == fail_request

    assert len(sessions) == 2
    assert sessions[0] is not sessions[1]
