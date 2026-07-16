from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine


@dataclass(frozen=True)
class DatabaseReadiness:
    configured: bool
    connected: bool
    schema_ready: bool
    detail: str


def build_engine(database_url: str | None) -> Engine | None:
    if not database_url:
        return None
    if database_url.startswith(("sqlite", "duckdb")):
        raise ValueError("PostgreSQL is required; SQLite and DuckDB are unsupported.")
    return create_engine(database_url, pool_pre_ping=True)


def check_readiness(engine: Engine | None) -> DatabaseReadiness:
    if engine is None:
        return DatabaseReadiness(False, False, False, "DATABASE_URL is not configured.")
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            tables = set(inspect(connection).get_table_names())
        ready = "schema_versions" in tables
        return DatabaseReadiness(True, True, ready, "ready" if ready else "Foundation migrations are not applied.")
    except Exception as exc:
        return DatabaseReadiness(True, False, False, f"Database unavailable: {exc.__class__.__name__}.")
