"""add latest recommendation fields to cases

Revision ID: 0002_case_latest_recommendation
Revises: 0001_initial_schema
Create Date: 2026-05-23
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_case_latest_recommendation"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cases", sa.Column("latest_recommendation_label", sa.String(length=128), nullable=True))
    op.add_column("cases", sa.Column("latest_risk_level", sa.String(length=64), nullable=True))
    op.add_column("cases", sa.Column("latest_recommendation_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("cases", sa.Column("latest_case_update_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("cases", "latest_case_update_id")
    op.drop_column("cases", "latest_recommendation_at")
    op.drop_column("cases", "latest_risk_level")
    op.drop_column("cases", "latest_recommendation_label")
