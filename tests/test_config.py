import pytest
from pydantic import ValidationError
from sqlalchemy.engine import make_url

from supportflow_ai.config import Settings


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("HOST", "PORT", "DB", "USER", "PASSWORD"):
        monkeypatch.delenv(f"POSTGRES_{name}", raising=False)


def test_settings_load_dotenv_and_prefer_environment(tmp_path, monkeypatch) -> None:
    dotenv = tmp_path / "test.env"
    dotenv.write_text(
        "POSTGRES_HOST=file-host\nPOSTGRES_PORT=5433\n"
        "POSTGRES_DB=test_db\nPOSTGRES_USER=test_user\n"
        "POSTGRES_PASSWORD=test_password\nUNRELATED_SETTING=ignored\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("POSTGRES_HOST", "env-host")

    settings = Settings(_env_file=dotenv)

    assert settings.postgres_host == "env-host"
    assert settings.postgres_port == 5433
    assert settings.postgres_db == "test_db"
    assert settings.postgres_user == "test_user"
    assert settings.postgres_password.get_secret_value() == "test_password"


def test_database_url_preserves_special_characters_and_masks_password() -> None:
    password = "test:p@ss/word%?#[]"
    settings = Settings(_env_file=None, postgres_password=password)

    url = settings.database_url
    assert url.drivername == "postgresql+psycopg"
    assert make_url(url.render_as_string(hide_password=False)).password == password
    assert password not in repr(settings)
    assert password not in str(url)


@pytest.mark.parametrize("port", [0, 65536])
def test_settings_reject_invalid_ports(port: int) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, postgres_password="test_password", postgres_port=port)


def test_password_is_required_without_a_dotenv_file() -> None:
    with pytest.raises(ValidationError, match="postgres_password"):
        Settings(_env_file=None)
