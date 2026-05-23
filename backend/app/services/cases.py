import json
from typing import Optional

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from backend.app.core.time import singapore_now
from backend.app.models import Case, CaseUpdate, Recommendation, RecommendationLabel, UserMode
from backend.app.schemas import CaseDetail, CaseOut, CaseUpdateOut, RecommendationOut, Summary


def generate_case_id(db: Session) -> str:
    today = singapore_now().strftime("%Y%m%d")
    prefix = f"CASE-{today}-"
    count = db.scalar(select(func.count()).select_from(Case).where(Case.case_id.like(f"{prefix}%"))) or 0
    return f"{prefix}{count + 1:04d}"


def create_case(db: Session, user_mode: str) -> Case:
    case = Case(case_id=generate_case_id(db), user_mode=UserMode(user_mode))
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def get_or_create_case(db: Session, case_id: Optional[str], user_mode: str) -> Case:
    if case_id:
        case = db.scalar(select(Case).where(Case.case_id == case_id))
        if case:
            return case
    return create_case(db, user_mode)


def search_cases(db: Session, query: Optional[str] = None, limit: int = 100) -> list[Case]:
    stmt = select(Case).order_by(desc(Case.updated_at)).limit(limit)
    if query:
        stmt = select(Case).where(Case.case_id.contains(query)).order_by(desc(Case.updated_at)).limit(limit)
    return list(db.scalars(stmt))


def refresh_latest_recommendation(case: Case) -> None:
    latest_update = max(case.updates, key=lambda item: (item.created_at, item.id), default=None)
    if not latest_update or not latest_update.recommendation:
        return

    rec = latest_update.recommendation
    case.latest_recommendation_label = rec.label.value
    case.latest_risk_level = rec.risk_level
    case.latest_recommendation_at = latest_update.created_at
    case.latest_case_update_id = latest_update.id


def backfill_case_latest_recommendations(db: Session) -> int:
    result = db.execute(
        select(Case).options(joinedload(Case.updates).joinedload(CaseUpdate.recommendation))
    )
    changed = 0
    for case in result.unique().scalars():
        previous = (
            case.latest_recommendation_label,
            case.latest_risk_level,
            case.latest_recommendation_at,
            case.latest_case_update_id,
        )
        refresh_latest_recommendation(case)
        current = (
            case.latest_recommendation_label,
            case.latest_risk_level,
            case.latest_recommendation_at,
            case.latest_case_update_id,
        )
        if current != previous:
            changed += 1
    if changed:
        db.commit()
    return changed


def append_update(db: Session, case: Case, user_mode: str, summary: Summary, rec: RecommendationOut) -> CaseUpdate:
    mode = UserMode(user_mode)
    update = CaseUpdate(case=case, user_mode=mode, summary_json=summary.model_dump_json())
    db.add(update)
    db.flush()
    stored_rec = Recommendation(
        case_update=update,
        user_mode=mode,
        label=RecommendationLabel(rec.label),
        risk_level=rec.risk_level,
        rationale=rec.rationale,
        contributing_indicators_json=json.dumps(rec.contributing_indicators),
        uncertainty_json=json.dumps(rec.uncertainty),
        guidance_refs_json=json.dumps(rec.guidance_refs),
    )
    db.add(stored_rec)
    now = singapore_now()
    case.updated_at = now
    case.latest_recommendation_label = rec.label
    case.latest_risk_level = rec.risk_level
    case.latest_recommendation_at = now
    case.latest_case_update_id = update.id
    db.commit()
    db.refresh(update)
    return update


def to_case_out(case: Case) -> CaseOut:
    return CaseOut(
        case_id=case.case_id,
        created_at=case.created_at,
        updated_at=case.updated_at,
        user_mode=case.user_mode.value,
        latest_recommendation_label=case.latest_recommendation_label,
        latest_risk_level=case.latest_risk_level,
        latest_recommendation_at=case.latest_recommendation_at,
        latest_case_update_id=case.latest_case_update_id,
    )


def to_update_out(update: CaseUpdate) -> CaseUpdateOut:
    rec = update.recommendation
    return CaseUpdateOut(
        id=update.id,
        created_at=update.created_at,
        user_mode=update.user_mode.value,
        summary=Summary.model_validate_json(update.summary_json),
        recommendation=RecommendationOut(
            label=rec.label.value,
            risk_level=rec.risk_level,
            rationale=rec.rationale,
            contributing_indicators=json.loads(rec.contributing_indicators_json),
            uncertainty=json.loads(rec.uncertainty_json),
            guidance_refs=json.loads(rec.guidance_refs_json),
            advisory_notice="This is a recommendation support tool and does not replace professional judgment.",
        ),
    )


def get_case_detail(db: Session, case_id: str) -> Optional[CaseDetail]:
    result = db.execute(
        select(Case)
        .where(Case.case_id == case_id)
        .options(joinedload(Case.updates).joinedload(CaseUpdate.recommendation))
    )
    case = result.unique().scalar_one_or_none()
    if not case:
        return None
    updates = sorted(case.updates, key=lambda item: item.created_at, reverse=True)
    base = to_case_out(case)
    return CaseDetail(**base.model_dump(), updates=[to_update_out(update) for update in updates])
