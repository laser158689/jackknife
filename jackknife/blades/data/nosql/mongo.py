"""Data blade — MongoDB connector (motor)."""

from __future__ import annotations

from typing import Any

from jackknife.blades.data.base import BaseNoSQLConnector
from jackknife.core.exceptions import NoSQLConnectorError
from jackknife.core.logging import get_logger

try:
    import motor.motor_asyncio as motor
except ImportError as exc:
    raise ImportError(
        "motor is not installed. Enable the data-nosql extra: poetry install -E data-nosql"
    ) from exc

log = get_logger(__name__)


class MongoConnector(BaseNoSQLConnector):
    """
    MongoDB connector using motor (async).

    Usage:
        async with MongoConnector("mongodb://localhost:27017", "mydb") as db:
            doc_id = await db.insert_one("users", {"name": "Alice"})
            doc = await db.find_one("users", {"_id": ObjectId(doc_id)})
    """

    def __init__(self, uri: str, database: str) -> None:
        self._uri = uri
        self._database_name = database
        self._client: motor.AsyncIOMotorClient | None = None
        self._db: Any = None

    async def connect(self) -> None:
        self._client = motor.AsyncIOMotorClient(self._uri)
        self._db = self._client[self._database_name]
        self._connected = True
        log.info("mongo_connected", database=self._database_name)

    async def disconnect(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
        self._connected = False

    def _col(self, collection: str) -> Any:
        if self._db is None:
            raise NoSQLConnectorError("Not connected. Use 'async with MongoConnector(...)'")
        return self._db[collection]

    async def insert_one(self, collection: str, document: dict[str, Any]) -> str:
        try:
            result = await self._col(collection).insert_one(document)
            return str(result.inserted_id)
        except Exception as exc:
            raise NoSQLConnectorError(f"insert_one failed: {exc}") from exc

    async def find_one(self, collection: str, filter: dict[str, Any]) -> dict[str, Any] | None:
        try:
            doc = await self._col(collection).find_one(filter)
            if doc and "_id" in doc:
                doc["_id"] = str(doc["_id"])
            return doc  # type: ignore[no-any-return]
        except Exception as exc:
            raise NoSQLConnectorError(f"find_one failed: {exc}") from exc

    async def find_many(
        self, collection: str, filter: dict[str, Any], limit: int = 100
    ) -> list[dict[str, Any]]:
        try:
            cursor = self._col(collection).find(filter).limit(limit)
            docs: list[dict[str, Any]] = await cursor.to_list(length=limit)
            for doc in docs:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
            return docs
        except Exception as exc:
            raise NoSQLConnectorError(f"find_many failed: {exc}") from exc

    async def update_one(
        self, collection: str, filter: dict[str, Any], update: dict[str, Any]
    ) -> bool:
        try:
            result = await self._col(collection).update_one(filter, {"$set": update})
            return bool(result.matched_count > 0)
        except Exception as exc:
            raise NoSQLConnectorError(f"update_one failed: {exc}") from exc

    async def delete_one(self, collection: str, filter: dict[str, Any]) -> bool:
        try:
            result = await self._col(collection).delete_one(filter)
            return bool(result.deleted_count > 0)
        except Exception as exc:
            raise NoSQLConnectorError(f"delete_one failed: {exc}") from exc

    async def health_check(self) -> bool:
        if self._client is None:
            return False
        try:
            await self._client.admin.command("ping")
            return True
        except Exception:
            return False
