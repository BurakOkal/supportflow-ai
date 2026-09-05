from io import StringIO
from pathlib import Path

from alembic import command
from alembic.config import Config

from supportflow_ai import config as configuration
from supportflow_ai.config import Settings

ROOT = Path(__file__).resolve().parents[1]


def test_initial_migration_renders_postgresql_schema_without_connecting(monkeypatch):
    password = "offline:test%password@"
    settings = Settings(_env_file=None, postgres_password=password)
    monkeypatch.setattr(configuration, "get_settings", lambda: settings)
    output = StringIO()
    config = Config(str(ROOT / "alembic.ini"), output_buffer=output)

    command.upgrade(config, "head", sql=True)

    sql = output.getvalue()
    assert "CREATE TABLE tickets" in sql
    assert "id UUID NOT NULL" in sql
    assert "subject VARCHAR(200) NOT NULL" in sql
    assert "description TEXT NOT NULL" in sql
    assert "created_at TIMESTAMP WITH TIME ZONE NOT NULL" in sql
    assert "updated_at TIMESTAMP WITH TIME ZONE NOT NULL" in sql
    assert "CREATE INDEX ix_tickets_customer_email" in sql
    assert "CONSTRAINT pk_tickets PRIMARY KEY (id)" in sql
    assert "CONSTRAINT ck_tickets_ticket_status CHECK" in sql
    assert password not in sql
