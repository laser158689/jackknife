"""
Memory blade — async write queue for concurrency-safe writes.

Problem:
    Multiple agents (Claude Code, Cursor, background scripts) may attempt
    to write to ChromaDB simultaneously. ChromaDB does not support
    transactional writes, so concurrent writes corrupt data or cause loss.

Solution:
    A single asyncio.Queue processes all writes serially.
    Reads remain concurrent (ChromaDB handles concurrent reads fine).

Usage:
    queue = MemoryWriteQueue(store=chroma_store)
    await queue.start()                     # Start background consumer task
    entry_id = await queue.enqueue(entry)   # Blocks until write completes
    await queue.stop()                      # Drain queue and shut down

Phase 2 note:
    This module is the interface contract. The ChromaDB implementation
    (chroma_store.py) is wired in during Phase 2.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from jackknife.blades.memory.base import BaseMemoryStore
from jackknife.blades.memory.models import MemoryEntry
from jackknife.core.logging import get_logger

log = get_logger(__name__)


@dataclass
class _WriteRequest:
    """Internal: a pending write operation with its completion future."""

    entry: MemoryEntry
    future: asyncio.Future[str] = field(init=False)

    def __post_init__(self) -> None:
        # Future is created by enqueue(), not here, to avoid event loop issues.
        # This field is set explicitly before the request is put on the queue.
        pass


class MemoryWriteQueue:
    """
    Serializes all write operations to a BaseMemoryStore.

    The queue consumer runs as a background asyncio Task.
    Writers await the future returned by enqueue(), blocking until
    the write is complete or the timeout is reached.
    """

    def __init__(self, store: BaseMemoryStore, max_queue_size: int = 1000) -> None:
        self._store = store
        self._queue: asyncio.Queue[_WriteRequest] = asyncio.Queue(maxsize=max_queue_size)
        self._consumer_task: asyncio.Task[None] | None = None
        self._running = False

    async def start(self) -> None:
        """Start the background write consumer."""
        self._running = True
        self._consumer_task = asyncio.create_task(self._consume(), name="memory-write-queue")
        log.info("memory_write_queue_started", max_size=self._queue.maxsize)

    async def stop(self) -> None:
        """Drain the queue and stop the consumer gracefully."""
        self._running = False
        await self._queue.join()  # Wait for all pending writes to complete
        if self._consumer_task:
            self._consumer_task.cancel()
        log.info("memory_write_queue_stopped")

    async def enqueue(self, entry: MemoryEntry, timeout: float = 30.0) -> str:
        """
        Enqueue a write operation.

        Blocks until the write completes or timeout is reached.
        Returns the assigned entry ID.

        Args:
            entry: The memory entry to store
            timeout: Seconds to wait before raising TimeoutError

        Returns:
            The assigned entry ID string

        Raises:
            TimeoutError: If the write takes longer than timeout seconds
            MemoryWriteError: If the underlying store raises an error
        """
        loop = asyncio.get_running_loop()
        future: asyncio.Future[str] = loop.create_future()
        request = _WriteRequest(entry=entry)
        request.future = future
        await self._queue.put(request)
        return await asyncio.wait_for(future, timeout=timeout)

    async def _consume(self) -> None:
        """Background consumer: process writes one at a time."""
        while self._running or not self._queue.empty():
            try:
                request = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                try:
                    entry_id = await self._store.store(request.entry)
                    request.future.set_result(entry_id)
                    log.debug("memory_write_complete", entry_id=entry_id)
                except Exception as exc:
                    request.future.set_exception(exc)
                    log.error("memory_write_failed", error=str(exc))
                finally:
                    self._queue.task_done()
            except TimeoutError:
                continue
