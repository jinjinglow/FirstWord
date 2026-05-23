import json
import re

from backend.app.models import RecommendationLabel
from backend.app.schemas import RecommendationOut, Summary
from backend.app.services.guidance import (
    GUIDANCE_REFERENCES,
    LOWER_RISK_TERMS,
    MODERATE_TERMS,
    SERIOUS_TERMS,
)

ADVISORY_NOTICE = "This is a recommendation support tool and does not replace professional judgment."


def _summary_text(summary: Summary) -> str:
    pieces = [
        summary.case_overview,
        *summary.key_concerns,
        *summary.observations,
        *summary.reported_statements,
        *summary.protective_factors,
        *summary.risk_indicators,
        *summary.recommended_follow_up,
        *summary.uncertainty,
    ]
    return "\n".join(p for p in pieces if p).lower()


def _matched_terms(text: str, terms: list[str]) -> list[str]:
    matched = []
    for term in terms:
        if re.search(rf"\b{re.escape(term)}\b", text):
            matched.append(term)
    return matched


def build_recommendation(summary: Summary, user_mode: str) -> RecommendationOut:
    text = _summary_text(summary)
    low = _matched_terms(text, LOWER_RISK_TERMS)
    moderate = _matched_terms(text, MODERATE_TERMS)
    serious = _matched_terms(text, SERIOUS_TERMS)

    summary_indicators = [item for item in summary.risk_indicators if item.strip()]
    uncertainty = [item for item in summary.uncertainty if item.strip()]
    if not summary_indicators and not low and not moderate and not serious:
        uncertainty.append("The available summary contains limited explicit risk indicators.")

    guidance_refs = ["sssg_carg", "tier_1"]
    if moderate:
        guidance_refs.append("tier_2")
    if serious:
        guidance_refs.extend(["child_protection", "physical"])
    if any(term in text for term in ["sexual", "molest", "rape", "grooming"]):
        guidance_refs.append("sexual")
    if "neglect" in text or "supervision" in text:
        guidance_refs.append("neglect")
    if any(term in text for term in ["emotional", "threatened", "humiliated", "fearful"]):
        guidance_refs.append("emotional")
    guidance_refs = list(dict.fromkeys(guidance_refs))

    contributing = [*summary_indicators, *[f"Matched guidance indicator: {term}" for term in serious + moderate + low]]

    if serious:
        label = RecommendationLabel.recommend_carg_review.value
        risk_level = "Serious child protection concern"
        rationale = (
            "The summary contains indicators aligned with serious child protection concerns in the bundled MSF "
            "guidance snapshot. A trained CARG user or designated child-protection personnel should review the "
            "concern promptly. The tool is not confirming abuse."
        )
    elif moderate or (user_mode == "SSSG" and summary_indicators):
        label = RecommendationLabel.escalate_tier_2.value
        risk_level = "Moderate child protection concern"
        rationale = (
            "The summary contains moderate safety or risk indicators. For an SSSG user, this supports discussion "
            "with the organisation's CARG-trained user. For a CARG user, it supports considering Tier 2 protective "
            "intervention pathways while applying professional judgment."
        )
    elif low:
        label = RecommendationLabel.tier_1_intervention.value
        risk_level = "Lower-risk family stress concern"
        rationale = (
            "The summary contains lower-risk family stress or support indicators aligned with Tier 1 community "
            "support. This supports offering or coordinating appropriate Tier 1 intervention while continuing "
            "to monitor for new or escalating child protection indicators."
        )
    else:
        label = RecommendationLabel.continue_monitoring.value
        risk_level = "No clear child protection escalation indicator"
        rationale = (
            "The summary contains insufficient explicit indicators for Tier 1 intervention, Tier 2 escalation, "
            "or child abuse escalation review. Continue monitoring, document changes, and revisit the concern "
            "if new information emerges."
        )

    if not contributing:
        contributing = ["No explicit indicator matched the bundled guidance snapshot."]

    return RecommendationOut(
        label=label,
        risk_level=risk_level,
        rationale=rationale,
        contributing_indicators=contributing,
        uncertainty=uncertainty,
        guidance_refs=[f"{key}: {GUIDANCE_REFERENCES[key]['title']}" for key in guidance_refs],
        advisory_notice=ADVISORY_NOTICE,
    )


def recommendation_to_storage(rec: RecommendationOut) -> dict[str, str]:
    return {
        "contributing_indicators_json": json.dumps(rec.contributing_indicators),
        "uncertainty_json": json.dumps(rec.uncertainty),
        "guidance_refs_json": json.dumps(rec.guidance_refs),
    }
