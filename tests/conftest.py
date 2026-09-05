from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from supportflow_ai.main import create_app
from supportflow_ai.repositories.ticket import InMemoryTicketRepository


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--postgres",
        action="store_true",
        default=False,
        help="Run PostgreSQL integration tests in a temporary schema.",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "postgres: requires PostgreSQL and the --postgres option"
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if not config.getoption("--postgres"):
        for item in items:
            if "postgres" in item.keywords:
                item.add_marker(pytest.mark.skip(reason="use --postgres to run"))


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app(InMemoryTicketRepository())) as test_client:
        yield test_client
