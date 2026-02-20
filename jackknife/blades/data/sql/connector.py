"""
Data blade — async SQL connector (SQLAlchemy).

Supports PostgreSQL (asyncpg), MySQL (aiomysql), and SQLite (aiosqlite)
through SQLAlchemy's asyncio extension. The database URL determines
which backend is used:

    sqlite+aiosqlite:///./app.db
    postgresql+asyncpg://user:pass@host/db
    mysql+aiomysql://user:pass@host/db
"""

from __future__ import annotations

from typing import Any

from jackknife.blades.data.base import BaseSQLConnector
from jackknife.core.exceptions import SQLConnectorError
from jackknife.core.logging import get_logger

try:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker
except ImportError as exc:
    raise ImportError(
        "SQLAlchemy asyncio not installed. " "Enable the data-sql extra: poetry install -E data-sql"
    ) from exc

log = get_logger(__name__)


class SQLConnector(BaseSQLConnector):
    """
    Async SQL connector using SQLAlchemy.

    Use as an async context manager for automatic connection management:
        async with SQLConnector(url) as db:
            rows = await db.fetch_all("SELECT * FROM users WHERE active = :active",
                                       {"active": True})
    """

    def __init__(self, url: str, echo: bool = False, pool_size: int = 5) -> None:
        self._url = url
        self._engine = create_async_engine(url, echo=echo, pool_pre_ping=True)
        self._session_factory: Any = sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )
        self._session: AsyncSession | None = None

    async def connect(self) -> None:
        self._session = self._session_factory()
        self._connected = True
        log.info("sql_connected", url=self._url.split("@")[-1])  # hide credentials

    async def disconnect(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None
        await self._engine.dispose()
        self._connected = False

    def _get_session(self) -> AsyncSession:
        if self._session is None:
            raise SQLConnectorError("Not connected. Use 'async with SQLConnector(url) as db'")
        return self._session

    async def execute(self, query: str, params: dict[str, Any] | None = None) -> Any:
        """Execute a statement (INSERT/UPDATE/DELETE). Returns CursorResult."""
        session = self._get_session()
        try:
            result = await session.execute(text(query), params or {})
            await session.commit()
            return result
        except Exception as exc:
            await session.rollback()
            raise SQLConnectorError(f"execute failed: {exc}") from exc

    async def execute_many(self, query: str, params_list: list[dict[str, Any]]) -> int:
        """Batch execute. Returns number of rows affected."""
        session = self._get_session()
        try:
            total = 0
            for params in params_list:
                result = await session.execute(text(query), params)
                total += result.rowcount or 0
            await session.commit()
            return total
        except Exception as exc:
            await session.rollback()
            raise SQLConnectorError(f"execute_many failed: {exc}") from exc

    async def fetch_one(
        self, query: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        session = self._get_session()
        try:
            result = await session.execute(text(query), params or {})
            row = result.mappings().first()
            return dict(row) if row else None
        except Exception as exc:
            raise SQLConnectorError(f"fetch_one failed: {exc}") from exc

    async def fetch_all(
        self, query: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        session = self._get_session()
        try:
            result = await session.execute(text(query), params or {})
            return [dict(row) for row in result.mappings().all()]
        except Exception as exc:
            raise SQLConnectorError(f"fetch_all failed: {exc}") from exc

    async def health_check(self) -> bool:
        try:
            await self.fetch_one("SELECT 1")
            return True
        except Exception:
            return False
