"""platform foundation"""
import sqlalchemy as sa

from alembic import op

revision = "0001_platform_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "outbox_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.String(128), nullable=False, unique=True),
        sa.Column("event_type", sa.String(160), nullable=False),
        sa.Column("aggregate_type", sa.String(80), nullable=False),
        sa.Column("aggregate_id", sa.String(128), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "inbox_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("consumer", sa.String(128), nullable=False),
        sa.Column("event_id", sa.String(128), nullable=False),
        sa.Column("event_type", sa.String(160), nullable=False),
        sa.Column("result_hash", sa.String(128), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("consumer", "event_id", name="uq_inbox_consumer_event"),
    )
    op.create_table(
        "idempotency_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scope", sa.String(180), nullable=False),
        sa.Column("key", sa.String(255), nullable=False),
        sa.Column("request_hash", sa.String(128), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("response_body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("scope", "key", name="uq_idempotency_scope_key"),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("action", sa.String(160), nullable=False),
        sa.Column("actor", sa.String(160), nullable=False),
        sa.Column("resource", sa.String(255), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("correlation_id", sa.String(128)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("idempotency_records")
    op.drop_table("inbox_events")
    op.drop_table("outbox_events")
