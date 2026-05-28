"""Initial schema — all application tables.

Revision ID: 001_initial
Revises:
Create Date: 2026-05-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=200), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_id", "users", ["id"])

    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("company", sa.String(length=200), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=False, server_default="Israel"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("requirements_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("skills_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("parsed_skills_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("skills_content_hash", sa.String(length=32), nullable=True),
        sa.Column("embedding_json", sa.Text(), nullable=True),
        sa.Column("embedding_hash", sa.String(length=32), nullable=True),
        sa.Column("embedding_method", sa.String(length=40), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=False, server_default="AI / Data"),
        sa.Column("employment_type", sa.String(length=50), nullable=False, server_default="Full-time"),
        sa.Column("salary_range", sa.String(length=100), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("language", sa.String(length=10), nullable=False, server_default="en"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("source", sa.String(length=50), nullable=False, server_default="seed"),
        sa.Column("external_id", sa.String(length=200), nullable=True),
        sa.Column("work_mode", sa.String(length=50), nullable=True),
        sa.Column("is_israel", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("location_tag", sa.String(length=30), nullable=True),
        sa.Column("posted_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_jobs_id", "jobs", ["id"])
    op.create_index("ix_jobs_source", "jobs", ["source"])
    op.create_index("ix_jobs_external_id", "jobs", ["external_id"])
    op.create_index("ix_jobs_is_israel", "jobs", ["is_israel"])

    op.create_table(
        "cv_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("full_name", sa.String(length=200), nullable=True),
        sa.Column("email", sa.String(length=200), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("years_experience", sa.Integer(), nullable=True),
        sa.Column("job_titles_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("skills_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("tools_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("technologies_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("languages_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("skills_confidence_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("source_filename", sa.String(length=500), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("extraction_method", sa.String(length=50), nullable=False, server_default="mock_heuristic"),
        sa.Column("embedding_json", sa.Text(), nullable=True),
        sa.Column("embedding_hash", sa.String(length=32), nullable=True),
        sa.Column("embedding_method", sa.String(length=40), nullable=True),
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("language", sa.String(length=10), nullable=False, server_default="en"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_cv_profiles_id", "cv_profiles", ["id"])
    op.create_index("ix_cv_profiles_user_id", "cv_profiles", ["user_id"])

    op.create_table(
        "user_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("email", sa.String(length=200), nullable=False, server_default="demo@example.com"),
        sa.Column("daily_digest_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("digest_hour", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("ui_language", sa.String(length=10), nullable=False, server_default="en"),
        sa.Column("min_match_score", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("preferred_job_keywords_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("last_digest_sent_at", sa.DateTime(), nullable=True),
        sa.Column("demo_mode", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("include_saved_jobs", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_user_settings_id", "user_settings", ["id"])
    op.create_index("ix_user_settings_user_id", "user_settings", ["user_id"], unique=True)

    op.create_table(
        "job_matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cv_profile_id", sa.Integer(), sa.ForeignKey("cv_profiles.id"), nullable=False),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("match_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("match_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("missing_skills_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("matched_skills_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("semantic_matches_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("score_breakdown_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("job_skills_debug_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("semantic_overlap", sa.Float(), nullable=False, server_default="0"),
        sa.Column("emailed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_job_matches_id", "job_matches", ["id"])
    op.create_index("ix_job_matches_cv_profile_id", "job_matches", ["cv_profile_id"])
    op.create_index("ix_job_matches_job_id", "job_matches", ["job_id"])

    op.create_table(
        "saved_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("user_id", "job_id", name="uq_saved_jobs_user_job"),
    )
    op.create_index("ix_saved_jobs_id", "saved_jobs", ["id"])
    op.create_index("ix_saved_jobs_user_id", "saved_jobs", ["user_id"])
    op.create_index("ix_saved_jobs_job_id", "saved_jobs", ["job_id"])

    op.create_table(
        "email_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("recipient", sa.String(length=200), nullable=False),
        sa.Column("subject", sa.String(length=300), nullable=False, server_default=""),
        sa.Column("match_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sent", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("preview_only", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("job_ids_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_email_logs_id", "email_logs", ["id"])

    op.create_table(
        "scheduler_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_name", sa.String(length=80), nullable=False, server_default="daily_digest"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="started"),
        sa.Column("message", sa.Text(), nullable=False, server_default=""),
        sa.Column("match_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sent", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("preview_only", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_scheduler_logs_id", "scheduler_logs", ["id"])


def downgrade() -> None:
    op.drop_table("scheduler_logs")
    op.drop_table("email_logs")
    op.drop_table("saved_jobs")
    op.drop_table("job_matches")
    op.drop_table("user_settings")
    op.drop_table("cv_profiles")
    op.drop_table("jobs")
    op.drop_table("users")
