"""create analysis_runs

Revision ID: 0001
Revises:
Create Date: 2026-10-22

Lifecycle invariants follow DATA_CONTRACTS §11. Every CHECK branch tests IS [NOT] NULL (never NULL
itself) so an absent value cannot satisfy a constraint by evaluating to NULL. The SQL is spelled out
here on purpose: a migration is a frozen record and must not import application code.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

_LIFECYCLE = (
    "(status = 'pending' AND analysis IS NULL AND completed_at_utc IS NULL AND error IS NULL"
    " AND failed_at_utc IS NULL AND failure_snapshot IS NULL AND started_at_utc IS NULL)"
    " OR (status = 'running' AND started_at_utc IS NOT NULL AND analysis IS NULL"
    " AND completed_at_utc IS NULL AND error IS NULL AND failed_at_utc IS NULL"
    " AND failure_snapshot IS NULL)"
    " OR (status = 'completed' AND analysis IS NOT NULL AND completed_at_utc IS NOT NULL"
    " AND started_at_utc IS NOT NULL AND error IS NULL AND failed_at_utc IS NULL"
    " AND failure_snapshot IS NULL)"
    " OR (status = 'failed' AND error IS NOT NULL AND failed_at_utc IS NOT NULL"
    " AND started_at_utc IS NOT NULL AND analysis IS NULL AND completed_at_utc IS NULL)"
)


def upgrade() -> None:
    op.create_table(
        "analysis_runs",
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("timeframe", sa.String(length=16), nullable=False),
        sa.Column("data_mode", sa.String(length=16), nullable=False),
        sa.Column("created_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("analysis", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("failure_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("analysis_id", name=op.f("pk_analysis_runs")),
        sa.CheckConstraint("status IN ('pending', 'running', 'completed', 'failed')", name=op.f("ck_analysis_runs_status_valid")),
        sa.CheckConstraint("symbol IN ('XAUUSD')", name=op.f("ck_analysis_runs_symbol_valid")),
        sa.CheckConstraint(
            "timeframe IN ('1m', '5m', '15m', '1h', '4h', '1d')", name=op.f("ck_analysis_runs_timeframe_valid")
        ),
        sa.CheckConstraint("data_mode IN ('fixture', 'live')", name=op.f("ck_analysis_runs_data_mode_valid")),
        sa.CheckConstraint(_LIFECYCLE, name=op.f("ck_analysis_runs_lifecycle")),
        sa.CheckConstraint(
            "started_at_utc IS NULL OR started_at_utc >= created_at_utc",
            name=op.f("ck_analysis_runs_started_after_created"),
        ),
        sa.CheckConstraint(
            "completed_at_utc IS NULL OR (started_at_utc IS NOT NULL AND completed_at_utc >= started_at_utc)",
            name=op.f("ck_analysis_runs_completed_after_started"),
        ),
        sa.CheckConstraint(
            "failed_at_utc IS NULL OR (started_at_utc IS NOT NULL AND failed_at_utc >= started_at_utc)",
            name=op.f("ck_analysis_runs_failed_after_started"),
        ),
        sa.CheckConstraint(
            "error IS NULL OR jsonb_typeof(error) = 'object'", name=op.f("ck_analysis_runs_error_is_object")
        ),
        sa.CheckConstraint(
            "analysis IS NULL OR jsonb_typeof(analysis) = 'object'",
            name=op.f("ck_analysis_runs_analysis_is_object"),
        ),
        sa.CheckConstraint(
            "failure_snapshot IS NULL OR jsonb_typeof(failure_snapshot) = 'object'",
            name=op.f("ck_analysis_runs_failure_snapshot_is_object"),
        ),
        sa.CheckConstraint(
            "failure_snapshot IS NULL OR status = 'failed'",
            name=op.f("ck_analysis_runs_failure_snapshot_only_failed"),
        ),
        sa.CheckConstraint(
            "analysis IS NULL OR coalesce((analysis ->> 'analysis_id') = analysis_id::text, false)",
            name=op.f("ck_analysis_runs_analysis_id_matches_row"),
        ),
    )
    op.create_index(
        "ix_analysis_runs_history",
        "analysis_runs",
        [sa.text("created_at_utc DESC"), sa.text("analysis_id DESC")],
    )
    op.create_index("ix_analysis_runs_request_id", "analysis_runs", ["request_id"])


def downgrade() -> None:
    op.drop_index("ix_analysis_runs_request_id", table_name="analysis_runs")
    op.drop_index("ix_analysis_runs_history", table_name="analysis_runs")
    op.drop_table("analysis_runs")
