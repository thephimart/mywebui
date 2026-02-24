"""Database connection management for multiple databases."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from mywebui import storage
from mywebui.config import get_config

_docs_engine: AsyncEngine | None = None
_docs_session_factory: async_sessionmaker[AsyncSession] | None = None

_audit_engine: AsyncEngine | None = None
_audit_session_factory: async_sessionmaker[AsyncSession] | None = None

_user_engines: dict[str, AsyncEngine] = {}
_user_session_factories: dict[str, async_sessionmaker[AsyncSession]] = {}


def get_docs_engine() -> AsyncEngine:
    """Get or create the docs database engine."""
    global _docs_engine
    if _docs_engine is None:
        config = get_config()
        storage.ensure_dirs()
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
        storage.ensure_dirs()
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
        _user_engines[username] = create_async_engine(
            storage.get_user_db_url(username),
            echo=False,
            future=True,
        )
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
