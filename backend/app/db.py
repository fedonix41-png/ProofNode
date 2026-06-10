import asyncpg
import logging
from typing import AsyncGenerator
from backend.app.config import settings

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        # If pool exists but was closed, reset it
        if self._pool is not None and getattr(self._pool, "_closed", False):
            self._pool = None

        if self._pool is None:
            try:
                self._pool = await asyncpg.create_pool(
                    user=settings.postgres_user,
                    password=settings.postgres_password,
                    database=settings.postgres_db,
                    host=settings.postgres_host,
                    port=settings.postgres_port,
                    min_size=2,
                    max_size=10
                )
                logger.info("Database connection pool initialized.")
            except Exception as e:
                logger.error(f"Failed to create database connection pool: {e}")
                raise e

    async def disconnect(self) -> None:
        if self._pool is not None:
            try:
                await self._pool.close()
            except Exception as e:
                logger.warning(f"Error during database pool close: {e}")
            finally:
                self._pool = None
                logger.info("Database connection pool closed.")

    async def get_connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        # Self-heal: check if pool is closed and reset it
        if self._pool is not None and getattr(self._pool, "_closed", False):
            self._pool = None

        if self._pool is None:
            await self.connect()

        async with self._pool.acquire() as conn:
            yield conn

db = Database()
