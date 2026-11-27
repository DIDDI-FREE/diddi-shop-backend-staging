from __future__ import annotations

import sqlalchemy as sa
from alembic.config import Config

from alembic import command


def test_alembic_upgrade_head_creates_the_persistent_schema(tmp_path, monkeypatch):
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'diddishop.db').as_posix()}"
    monkeypatch.setenv("DIDDI_SHOP_DATABASE_URL", database_url)

    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")

    engine = sa.create_engine(database_url.replace("+aiosqlite", ""))
    try:
        tables = set(sa.inspect(engine).get_table_names())
    finally:
        engine.dispose()

    assert "alembic_version" in tables
    assert {
        "outbox_events",
        "inbox_events",
        "idempotency_records",
        "audit_events",
        "shops",
        "products",
        "stock_operations",
        "carts",
        "checkouts",
        "orders",
        "claims",
        "delivery_projections",
    } <= tables
