"""add tier 1 intervention recommendation outcome

Revision ID: 0003_add_tier_1_intervention_outcome
Revises: 0002_case_latest_recommendation
Create Date: 2026-05-23
"""

revision = "0003_add_tier_1_intervention_outcome"
down_revision = "0002_case_latest_recommendation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite stores SQLAlchemy Enum values as text by default in this project,
    # so no table rewrite is required for existing local databases.
    pass


def downgrade() -> None:
    pass
