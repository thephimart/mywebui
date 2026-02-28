"""Database connection management for multiple databases."""

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from mywebui import storage
from mywebui.config import get_config

_docs_engine: AsyncEngine | None = None
_docs_session_factory: async_sessionmaker[AsyncSession] | None = None

_audit_engine: AsyncEngine | None = None
_audit_session_factory: async_sessionmaker[AsyncSession] | None = None

_user_engines: dict[str, AsyncEngine] = {}
_user_session_factories: dict[str, async_sessionmaker[AsyncSession]] = {}


def upgrade_docs_db(db_url: str) -> None:
    """Upgrade docs database to latest schema using Alembic.

    Args:
        db_url: The database URL to upgrade.
    """
    from alembic import command
    from alembic.config import Config

    sync_url = db_url.replace("sqlite+aiosqlite://", "sqlite://")

    alembic_cfg = Config("alembic_docs.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", sync_url)

    try:
        command.upgrade(alembic_cfg, "head")
    except Exception as e:
        raise RuntimeError(f"Docs database upgrade failed: {e}") from e


def upgrade_user_db(db_url: str) -> None:
    """Upgrade user database to latest schema using Alembic.

    Args:
        db_url: The database URL to upgrade.
    """
    from alembic import command
    from alembic.config import Config

    sync_url = db_url.replace("sqlite+aiosqlite://", "sqlite://")

    alembic_cfg = Config("alembic_users.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", sync_url)

    try:
        command.upgrade(alembic_cfg, "head")
    except Exception as e:
        raise RuntimeError(f"User database upgrade failed: {e}") from e


def stamp_db(db_url: str, is_user_db: bool, is_audit_db: bool = False) -> None:
    """Stamp a database with head revision without running migrations.

    Args:
        db_url: The database URL to stamp.
        is_user_db: True for user DB, False for docs DB.
        is_audit_db: True for audit DB.
    """
    from alembic import command
    from alembic.config import Config

    sync_url = db_url.replace("sqlite+aiosqlite://", "sqlite://")

    if is_audit_db:
        ini_file = "alembic_audit.ini"
    else:
        ini_file = "alembic_users.ini" if is_user_db else "alembic_docs.ini"
    alembic_cfg = Config(ini_file)
    alembic_cfg.set_main_option("sqlalchemy.url", sync_url)

    try:
        command.stamp(alembic_cfg, "head")
    except Exception as e:
        raise RuntimeError(f"Database stamp failed: {e}") from e


def has_alembic_version_table(db_url: str) -> bool:
    """Check if the database has an alembic_version table.

    Args:
        db_url: The database URL to check.

    Returns:
        True if the alembic_version table exists, False otherwise.
    """
    import sqlite3

    db_path = db_url.replace("sqlite+aiosqlite:///", "")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
        result = cursor.fetchone() is not None
        conn.close()
        return result
    except Exception:
        return False


def database_exists(db_url: str) -> bool:
    """Check if a database file exists.

    Args:
        db_url: The database URL to check.

    Returns:
        True if the database file exists, False otherwise.
    """
    db_path = db_url.replace("sqlite+aiosqlite:///", "")
    return Path(db_path).exists()


def _sync_create_tables(db_url: str, is_user_db: bool, is_audit_db: bool = False) -> None:
    """Synchronously create tables using sync SQLAlchemy.

    This is only for initial bootstrap of new databases.
    Uses sync engine to avoid async event loop issues.

    Args:
        db_url: The database URL.
        is_user_db: True for user DB, False for docs DB.
        is_audit_db: True for audit DB.
    """
    from sqlalchemy import create_engine

    from mywebui.db.models import AuditEvent
    from mywebui.db.models import Base as DocsBase
    from mywebui.db.user_models import Base as UserBase

    sync_url = db_url.replace("sqlite+aiosqlite://", "sqlite://")
    engine = create_engine(sync_url, echo=False)

    try:
        if is_audit_db:
            AuditEvent.metadata.create_all(engine)
        else:
            base = UserBase if is_user_db else DocsBase
            base.metadata.create_all(engine)
    finally:
        engine.dispose()


def init_docs_db() -> None:
    """Initialize the docs database with Alembic or create_all for new DBs."""
    storage.ensure_dirs()
    db_url = storage.get_docs_db_url()

    if database_exists(db_url):
        if not has_alembic_version_table(db_url):
            stamp_db(db_url, is_user_db=False)
        else:
            upgrade_docs_db(db_url)
    else:
        _sync_create_tables(db_url, is_user_db=False)
        stamp_db(db_url, is_user_db=False)


def upgrade_audit_db(db_url: str) -> None:
    """Upgrade audit database to latest schema using Alembic.

    Args:
        db_url: The database URL to upgrade.
    """
    from alembic import command
    from alembic.config import Config

    sync_url = db_url.replace("sqlite+aiosqlite://", "sqlite://")

    alembic_cfg = Config("alembic_audit.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", sync_url)

    try:
        command.upgrade(alembic_cfg, "head")
    except Exception as e:
        raise RuntimeError(f"Audit database upgrade failed: {e}") from e


def init_audit_db() -> None:
    """Initialize the audit database with Alembic or create_all for new DBs."""
    storage.ensure_dirs()
    db_url = storage.get_audit_db_url()

    if database_exists(db_url):
        if not has_alembic_version_table(db_url):
            stamp_db(db_url, is_user_db=False, is_audit_db=True)
        else:
            upgrade_audit_db(db_url)
    else:
        _sync_create_tables(db_url, is_user_db=False, is_audit_db=True)
        stamp_db(db_url, is_user_db=False, is_audit_db=True)


def init_user_db(username: str) -> None:
    """Initialize a user database with Alembic or create_all for new DBs.

    Args:
        username: The username for the user database.
    """
    storage.ensure_user_dir(username)
    db_url = storage.get_user_db_url(username)

    if database_exists(db_url):
        if not has_alembic_version_table(db_url):
            stamp_db(db_url, is_user_db=True)
        else:
            upgrade_user_db(db_url)
    else:
        _sync_create_tables(db_url, is_user_db=True)
        stamp_db(db_url, is_user_db=True)


def get_docs_engine() -> AsyncEngine:
    """Get or create the docs database engine."""
    global _docs_engine
    if _docs_engine is None:
        config = get_config()
        _docs_engine = create_async_engine(
            storage.get_docs_db_url(),
            echo=config.debug,
            future=True,
        )
    return _docs_engine


def get_docs_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the docs session factory."""
    global _docs_session_factory
    if _docs_session_factory is None:
        engine = get_docs_engine()
        _docs_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _docs_session_factory


async def get_docs_db() -> AsyncGenerator[AsyncSession, None]:
    """Get a docs database session."""
    factory = get_docs_session_factory()
    async with factory() as session:
        yield session


DocsDb = Annotated[AsyncSession, Depends(get_docs_db)]


def get_audit_engine() -> AsyncEngine:
    """Get or create the audit database engine."""
    global _audit_engine
    if _audit_engine is None:
        config = get_config()
        _audit_engine = create_async_engine(
            storage.get_audit_db_url(),
            echo=config.debug,
            future=True,
        )
    return _audit_engine


def get_audit_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the audit session factory."""
    global _audit_session_factory
    if _audit_session_factory is None:
        engine = get_audit_engine()
        _audit_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _audit_session_factory


async def get_audit_db() -> AsyncGenerator[AsyncSession, None]:
    """Get an audit database session."""
    factory = get_audit_session_factory()
    async with factory() as session:
        yield session


AuditDb = Annotated[AsyncSession, Depends(get_audit_db)]


def get_user_engine(username: str) -> AsyncEngine:
    """Get or create a user database engine."""
    if username not in _user_engines:
        storage.ensure_user_dir(username)
        init_user_db(username)
        engine = create_async_engine(
            storage.get_user_db_url(username),
            echo=False,
            future=True,
        )
        _user_engines[username] = engine
    return _user_engines[username]


def get_user_session_factory(username: str) -> async_sessionmaker[AsyncSession]:
    """Get or create a user session factory."""
    if username not in _user_session_factories:
        engine = get_user_engine(username)
        _user_session_factories[username] = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _user_session_factories[username]


async def get_user_db(username: str) -> AsyncGenerator[AsyncSession, None]:
    """Get a user database session."""
    factory = get_user_session_factory(username)
    async with factory() as session:
        yield session
