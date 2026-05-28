"""Add user_id to email_logs and scheduler_logs for per-user digest audit."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_digest_user_logs"
down_revision: Union[str, None] = "002_job_tags_collector"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("email_logs", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_index("ix_email_logs_user_id", "email_logs", ["user_id"])
    op.create_foreign_key(
        "fk_email_logs_user_id",
        "email_logs",
        "users",
        ["user_id"],
        ["id"],
    )

    op.add_column("scheduler_logs", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_index("ix_scheduler_logs_user_id", "scheduler_logs", ["user_id"])
    op.create_foreign_key(
        "fk_scheduler_logs_user_id",
        "scheduler_logs",
        "users",
        ["user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_scheduler_logs_user_id", "scheduler_logs", type_="foreignkey")
    op.drop_index("ix_scheduler_logs_user_id", table_name="scheduler_logs")
    op.drop_column("scheduler_logs", "user_id")

    op.drop_constraint("fk_email_logs_user_id", "email_logs", type_="foreignkey")
    op.drop_index("ix_email_logs_user_id", table_name="email_logs")
    op.drop_column("email_logs", "user_id")
