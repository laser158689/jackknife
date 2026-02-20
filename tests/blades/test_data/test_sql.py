"""Tests for SQLConnector using SQLite in-memory."""

from __future__ import annotations

import pytest

from jackknife.blades.data.sql.connector import SQLConnector


@pytest.fixture
async def db():
    conn = SQLConnector(url="sqlite+aiosqlite:///:memory:")
    async with conn:
        await conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, active INTEGER)")
        yield conn


async def test_execute_insert(db):
    result = await db.execute(
        "INSERT INTO users (name, active) VALUES (:name, :active)", {"name": "Alice", "active": 1}
    )
    assert result is not None


async def test_fetch_one(db):
    await db.execute(
        "INSERT INTO users (name, active) VALUES (:name, :active)", {"name": "Bob", "active": 1}
    )
    row = await db.fetch_one("SELECT name FROM users WHERE name = :name", {"name": "Bob"})
    assert row is not None
    assert row["name"] == "Bob"


async def test_fetch_one_missing(db):
    row = await db.fetch_one("SELECT * FROM users WHERE name = :name", {"name": "nobody"})
    assert row is None


async def test_fetch_all(db):
    for name in ["Alice", "Bob", "Carol"]:
        await db.execute(
            "INSERT INTO users (name, active) VALUES (:name, :active)", {"name": name, "active": 1}
        )
    rows = await db.fetch_all("SELECT * FROM users ORDER BY name")
    assert len(rows) == 3
    assert rows[0]["name"] == "Alice"


async def test_execute_many(db):
    params_list = [{"name": f"user{i}", "active": 1} for i in range(5)]
    count = await db.execute_many(
        "INSERT INTO users (name, active) VALUES (:name, :active)", params_list
    )
    assert count == 5


async def test_health_check(db):
    assert await db.health_check() is True
