from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

UserMode = Literal["SSSG", "CARG"]


class Summary(BaseModel):
    case_overview: str = ""
    key_concerns: list[str] = Field(default_factory=list)
    observations: list[str] = Field(default_factory=list)
    reported_statements: list[str] = Field(default_factory=list)
    protective_factors: list[str] = Field(default_factory=list)
    risk_indicators: list[str] = Field(default_factory=list)
    recommended_follow_up: list[str] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list)


class RecommendationOut(BaseModel):
    label: str
    risk_level: str
    rationale: str
    contributing_indicators: list[str]
    uncertainty: list[str]
    guidance_refs: list[str]
    advisory_notice: str


class CaseCreate(BaseModel):
    user_mode: UserMode


class CaseOut(BaseModel):
    case_id: str
    created_at: datetime
    updated_at: datetime
    user_mode: UserMode
    latest_recommendation_label: Optional[str] = None
    latest_risk_level: Optional[str] = None
    latest_recommendation_at: Optional[datetime] = None
    latest_case_update_id: Optional[int] = None


class CaseUpdateOut(BaseModel):
    id: int
    created_at: datetime
    user_mode: UserMode
    summary: Summary
    recommendation: RecommendationOut


class CaseDetail(CaseOut):
    updates: list[CaseUpdateOut]


class ProcessResponse(BaseModel):
    case_id: str
    update: CaseUpdateOut


class AiHealth(BaseModel):
    ollama_running: bool
    model_available: bool
    model_name: str
    message: str
