from collections.abc import Iterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pgvector.psycopg import register_vector
import psycopg
from psycopg_pool import ConnectionPool

from core.config import get_settings

settings = get_settings()


def configure_connection(connection: psycopg.Connection) -> None:
  register_vector(connection)


pool = ConnectionPool(
    conninfo=settings.sync_database_url,
    min_size=2,
    max_size=10,
    configure=configure_connection,
    open=False,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
  pool.open()
  yield
  pool.close()


def get_db() -> Iterator[psycopg.Connection]:
  with pool.connection() as connection:
    yield connection