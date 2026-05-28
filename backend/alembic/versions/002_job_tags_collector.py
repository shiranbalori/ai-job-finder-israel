"""Add job tags and collector audit logs.

Revision ID: 002_job_tags_collector
Revises: 001_initial
Create Date: 2026-05-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_job_tags_collector"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("tags_json", sa.Text(), nullable=False, server_default="[]"))

    op.create_table(
        "job_collector_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="started"),
        sa.Column("sources_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("total_fetched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_matched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("errors_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("message", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_job_collector_logs_id", "job_collector_logs", ["id"])


def downgrade() -> None:
    op.drop_index("ix_job_collector_logs_id", table_name="job_collector_logs")
    op.drop_table("job_collector_logs")
    op.drop_column("jobs", "tags_json")
