from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.time import singapore_now
from backend.app.db.session import Base


class UserMode(str, Enum):
    sssg = "SSSG"
    carg = "CARG"


class RecommendationLabel(str, Enum):
    continue_monitoring = "Continue Monitoring"
    tier_1_intervention = "Tier 1 Intervention"
    escalate_tier_2 = "Escalate from Tier 1 to Tier 2"
    recommend_carg_review = "Recommend Child Abuse Escalation Review"


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=singapore_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=singapore_now)
    user_mode: Mapped[UserMode] = mapped_column(SqlEnum(UserMode), index=True)
    latest_recommendation_label: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    latest_risk_level: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    latest_recommendation_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    latest_case_update_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    updates: Mapped[list["CaseUpdate"]] = relationship(back_populates="case", cascade="all, delete-orphan")


class CaseUpdate(Base):
    __tablename__ = "case_updates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id_fk: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=singapore_now)
    user_mode: Mapped[UserMode] = mapped_column(SqlEnum(UserMode), index=True)
    summary_json: Mapped[str] = mapped_column(Text)

    case: Mapped[Case] = relationship(back_populates="updates")
    recommendation: Mapped["Recommendation"] = relationship(
        back_populates="case_update",
        cascade="all, delete-orphan",
        uselist=False,
    )


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_update_id: Mapped[int] = mapped_column(ForeignKey("case_updates.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=singapore_now)
    user_mode: Mapped[UserMode] = mapped_column(SqlEnum(UserMode), index=True)
    label: Mapped[RecommendationLabel] = mapped_column(SqlEnum(RecommendationLabel), index=True)
    risk_level: Mapped[str] = mapped_column(String(64))
    rationale: Mapped[str] = mapped_column(Text)
    contributing_indicators_json: Mapped[str] = mapped_column(Text)
    uncertainty_json: Mapped[str] = mapped_column(Text)
    guidance_refs_json: Mapped[str] = mapped_column(Text)

    case_update: Mapped[CaseUpdate] = relationship(back_populates="recommendation")
