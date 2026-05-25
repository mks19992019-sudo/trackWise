from __future__ import annotations
import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DEFAULT_POSTGRES_DSN = os.getenv("DATABASE_URL")
POSTGRES_DSN = os.getenv("POSTGRES_DSN", DEFAULT_POSTGRES_DSN)
POSTGRES_MIN_POOL_SIZE = int(os.getenv("POSTGRES_MIN_POOL_SIZE", "1"))
POSTGRES_MAX_POOL_SIZE = int(os.getenv("POSTGRES_MAX_POOL_SIZE", "10"))

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS expenses (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    currency TEXT NOT NULL CHECK (currency = UPPER(currency) AND char_length(currency) = 3),
    merchant TEXT,
    notes TEXT,
    spent_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_expenses_user_spent_at
    ON expenses (user_id, spent_at DESC);

CREATE INDEX IF NOT EXISTS idx_expenses_user_category_spent_at
    ON expenses (user_id, category, spent_at DESC);

CREATE INDEX IF NOT EXISTS idx_expenses_user_currency_spent_at
    ON expenses (user_id, currency, spent_at DESC);

CREATE INDEX IF NOT EXISTS idx_expenses_search_document
    ON expenses
    USING GIN (
        to_tsvector(
            'simple',
            coalesce(description, '')
            || ' '
            || category
            || ' '
            || coalesce(merchant, '')
            || ' '
            || coalesce(notes, '')
        )
    );

CREATE TABLE IF NOT EXISTS budgets (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    category TEXT,
    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    currency TEXT NOT NULL CHECK (currency = UPPER(currency) AND char_length(currency) = 3),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL CHECK (period_end >= period_start),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_budgets_user_period
    ON budgets (user_id, period_start, period_end);

CREATE INDEX IF NOT EXISTS idx_budgets_user_category_period
    ON budgets (user_id, category, period_start, period_end);

CREATE INDEX IF NOT EXISTS idx_budgets_user_currency_period
    ON budgets (user_id, currency, period_start, period_end);
"""

_pool: asyncpg.Pool | None = None
_pool_loop: asyncio.AbstractEventLoop | None = None
_pool_lock = asyncio.Lock()


async def get_db_pool() -> asyncpg.Pool:
    global _pool, _pool_loop
    current_loop = asyncio.get_running_loop()

    if _pool is not None and _pool_loop is current_loop:
        return _pool

    async with _pool_lock:
        if _pool is not None and _pool_loop is not current_loop:
            _pool.terminate()
            _pool = None
            _pool_loop = None

        if _pool is None:
            _pool = await asyncpg.create_pool(
                dsn=POSTGRES_DSN,
                min_size=POSTGRES_MIN_POOL_SIZE,
                max_size=POSTGRES_MAX_POOL_SIZE,
            )
            _pool_loop = current_loop

    return _pool


async def initialize_database() -> asyncpg.Pool:
    pool = await get_db_pool()

    async with pool.acquire() as connection:
        await connection.execute(SCHEMA_SQL)

    return pool


async def close_db_pool() -> None:
    global _pool, _pool_loop

    async with _pool_lock:
        if _pool is not None:
            current_loop = asyncio.get_running_loop()

            if _pool_loop is current_loop:
                await _pool.close()
            else:
                _pool.terminate()

            _pool = None
            _pool_loop = None
