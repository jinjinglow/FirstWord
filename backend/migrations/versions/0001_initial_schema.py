"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-23
"""
from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    user_mode = sa.Enum("sssg", "carg", name="usermode")
    recommendation_label = sa.Enum(
        "continue_monitoring",
        "tier_1_intervention",
        "escalate_tier_2",
        "recommend_carg_review",
        name="recommendationlabel",
    )

    op.create_table(
        "cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_mode", user_mode, nullable=False),
    )
    op.create_index("ix_cases_case_id", "cases", ["case_id"], unique=True)
    op.create_index("ix_cases_user_mode", "cases", ["user_mode"])

    op.create_table(
        "case_updates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id_fk", sa.Integer(), sa.ForeignKey("cases.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_mode", user_mode, nullable=False),
        sa.Column("summary_json", sa.Text(), nullable=False),
    )
    op.create_index("ix_case_updates_case_id_fk", "case_updates", ["case_id_fk"])
    op.create_index("ix_case_updates_user_mode", "case_updates", ["user_mode"])

    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_update_id", sa.Integer(), sa.ForeignKey("case_updates.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_mode", user_mode, nullable=False),
        sa.Column("label", recommendation_label, nullable=False),
        sa.Column("risk_level", sa.String(length=64), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("contributing_indicators_json", sa.Text(), nullable=False),
        sa.Column("uncertainty_json", sa.Text(), nullable=False),
        sa.Column("guidance_refs_json", sa.Text(), nullable=False),
    )
    op.create_index("ix_recommendations_case_update_id", "recommendations", ["case_update_id"])
    op.create_index("ix_recommendations_label", "recommendations", ["label"])
    op.create_index("ix_recommendations_user_mode", "recommendations", ["user_mode"])


def downgrade() -> None:
    op.drop_index("ix_recommendations_user_mode", table_name="recommendations")
    op.drop_index("ix_recommendations_label", table_name="recommendations")
    op.drop_index("ix_recommendations_case_update_id", table_name="recommendations")
    op.drop_table("recommendations")
    op.drop_index("ix_case_updates_user_mode", table_name="case_updates")
    op.drop_index("ix_case_updates_case_id_fk", table_name="case_updates")
    op.drop_table("case_updates")
    op.drop_index("ix_cases_user_mode", table_name="cases")
    op.drop_index("ix_cases_case_id", table_name="cases")
    op.drop_table("cases")
