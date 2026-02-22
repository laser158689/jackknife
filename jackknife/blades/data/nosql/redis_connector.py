"""
Data blade — Redis connector.

Redis has a key-value / hash interface rather than documents, so
this class extends BaseDataConnector directly with Redis-appropriate
methods rather than the document-store-oriented BaseNoSQLConnector.
"""

from __future__ import annotations

from typing import Any

from jackknife.blades.data.base import BaseDataConnector
from jackknife.core.exceptions import NoSQLConnectorError
from jackknife.core.logging import get_logger

try:
    import redis.asyncio as aioredis
except ImportError as exc:
    raise ImportError(
        "redis[asyncio] is not installed. Enable the data-nosql extra: poetry install -E data-nosql"
    ) from exc

log = get_logger(__name__)


class RedisConnector(BaseDataConnector):
    """
    Async Redis connector.

    Wraps redis.asyncio with the jackknife connector lifecycle
    (connect/disconnect/health_check) and a clean typed API.
    """

    def __init__(self, url: str = "redis://localhost:6379", db: int = 0) -> None:
        self._url = url
        self._db = db
        self._client: aioredis.Redis | None = None  # type: ignore[type-arg]

    async def connect(self) -> None:
        self._client = aioredis.from_url(self._url, db=self._db, decode_responses=True)
        self._connected = True
        log.info("redis_connected", url=self._url)

    async def disconnect(self) -> None:
        if self._client:
            await self._client.aclose()  # type: ignore[attr-defined]
            self._client = None
        self._connected = False

    def _r(self) -> aioredis.Redis:  # type: ignore[type-arg]
        if self._client is None:
            raise NoSQLConnectorError("Not connected. Use 'async with RedisConnector(...)'")
        return self._client

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        """Set a string value. ex = TTL in seconds."""
        try:
            await self._r().set(key, value, ex=ex)
        except Exception as exc:
            raise NoSQLConnectorError(f"set({key!r}) failed: {exc}") from exc

    async def get(self, key: str) -> str | None:
        """Get a string value. Returns None if key doesn't exist."""
        try:
            return await self._r().get(key)
        except Exception as exc:
            raise NoSQLConnectorError(f"get({key!r}) failed: {exc}") from exc

    async def delete(self, *keys: str) -> int:
        """Delete keys. Returns number of keys deleted."""
        try:
            return int(await self._r().delete(*keys))
        except Exception as exc:
            raise NoSQLConnectorError(f"delete failed: {exc}") from exc

    async def exists(self, *keys: str) -> int:
        """Returns count of keys that exist."""
        try:
            return int(await self._r().exists(*keys))
        except Exception as exc:
            raise NoSQLConnectorError(f"exists failed: {exc}") from exc

    async def hset(self, name: str, mapping: dict[str, Any]) -> int:
        """Set multiple hash fields."""
        try:
            return int(await self._r().hset(name, mapping=mapping))  # type: ignore[arg-type]
        except Exception as exc:
            raise NoSQLConnectorError(f"hset({name!r}) failed: {exc}") from exc

    async def hget(self, name: str, key: str) -> str | None:
        """Get a hash field value."""
        try:
            return await self._r().hget(name, key)
        except Exception as exc:
            raise NoSQLConnectorError(f"hget({name!r}, {key!r}) failed: {exc}") from exc

    async def hgetall(self, name: str) -> dict[str, str]:
        """Get all hash fields and values."""
        try:
            result = await self._r().hgetall(name)
            return dict(result)
        except Exception as exc:
            raise NoSQLConnectorError(f"hgetall({name!r}) failed: {exc}") from exc

    async def expire(self, key: str, seconds: int) -> bool:
        """Set TTL on a key."""
        try:
            return bool(await self._r().expire(key, seconds))
        except Exception as exc:
            raise NoSQLConnectorError(f"expire({key!r}) failed: {exc}") from exc

    async def health_check(self) -> bool:
        try:
            return bool(await self._r().ping())
        except Exception:
            return False
