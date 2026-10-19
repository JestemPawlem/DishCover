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
    open=False
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open()
    with pool.connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                CREATE EXTENSION IF NOT EXISTS vector;
                '''
            )
            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                '''
            )
            cursor.execute(
                '''
                CREATE TABLE IF NOT EXISTS user_recipe_interactions (
                    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
                    recipe_id BIGINT REFERENCES recipes(id) ON DELETE CASCADE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, recipe_id)
                );
                '''
            )
            connection.commit()
    yield
    pool.close()


def get_db() -> Iterator[psycopg.Connection]:
    with pool.connection() as connection:
        yield connection