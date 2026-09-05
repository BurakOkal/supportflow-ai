from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from supportflow_ai.config import get_settings


@lru_cache
def get_engine() -> Engine:
    # Neither settings nor database connections are needed at import/startup.
    return create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
        hide_parameters=True,
        connect_args={"connect_timeout": 5},
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_session() -> Iterator[Session]:
    with get_session_factory()() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
