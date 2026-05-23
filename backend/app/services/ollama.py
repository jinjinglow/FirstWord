import json
import logging
import re

import httpx

from backend.app.core.config import get_settings
from backend.app.schemas import AiHealth, Summary

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You support professional child-safety documentation in Singapore.
You must not diagnose abuse, confirm abuse, make criminal accusations, invent facts, or override human judgment.
Use only the supplied transcript and the approved guidance summary.
Correct obvious transcription errors, remove filler words, and produce structured documentation.
State uncertainty explicitly where information is unclear, missing, or unsupported.
Return strict JSON only with these keys:
case_overview, key_concerns, observations, reported_statements, protective_factors, risk_indicators, recommended_follow_up, uncertainty.
Each key except case_overview must be an array of concise strings. case_overview must be a concise string.
Do not include markdown fences, commentary, or any text outside the JSON object.
"""

GUIDANCE_CONTEXT = """Approved guidance scope:
- SSSG users are frontline professionals such as teachers, healthcare workers, and social workers who use screening support to decide whether to consult a trained CARG user.
- CARG users are designated trained personnel who use the Child Abuse Reporting Guide to support decisions on whether to report concerns to NAVH or take alternative action for less serious child protection concerns.
- Tier 1 concerns are lower safety and risk concerns handled by community agencies, including family stress that may affect a child.
- Tier 2 concerns are moderate safety and risk concerns supported by specialist agencies.
- Serious child protection concerns may include significant physical injury indicators, sexual abuse concerns, severe neglect, imminent danger, or other high-risk safety concerns.
"""


async def check_ollama() -> AiHealth:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(f"{settings.ollama_base_url}/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            names = {model.get("name") for model in models}
            available = settings.ollama_model in names
            return AiHealth(
                ollama_running=True,
                model_available=available,
                model_name=settings.ollama_model,
                message="Ollama is running." if available else "Ollama is running, but the configured model is not available.",
            )
    except Exception as exc:
        logger.info("Ollama health check failed: %s", exc)
        return AiHealth(
            ollama_running=False,
            model_available=False,
            model_name=settings.ollama_model,
            message="Ollama is not reachable on the configured local URL.",
        )


async def summarise_transcript(transcript: str) -> Summary:
    settings = get_settings()
    prompt = f"{GUIDANCE_CONTEXT}\n\nTranscript:\n{transcript}"
    payload = {
        "model": settings.ollama_model,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "options": {
            "temperature": 0.1,
            "top_p": 0.8,
            "num_ctx": settings.ollama_num_ctx,
            "num_predict": settings.ollama_num_predict,
        },
        "keep_alive": "10m",
    }

    logger.info(
        "Sending transcript to Ollama for summary: transcript_chars=%s num_ctx=%s num_predict=%s",
        len(transcript),
        settings.ollama_num_ctx,
        settings.ollama_num_predict,
    )

    async with httpx.AsyncClient(timeout=settings.ollama_timeout_seconds) as client:
        response = await client.post(f"{settings.ollama_base_url}/api/chat", json=payload)
        response.raise_for_status()
        content = response.json()["message"]["content"]

    try:
        return Summary.model_validate(_loads_json_object(content))
    except Exception as exc:
        logger.warning(
            "Ollama returned non-conforming summary JSON: %s response_chars=%s",
            exc,
            len(content),
        )
        return Summary(
            case_overview="The transcript was processed, but the structured response could not be fully parsed.",
            key_concerns=[],
            observations=[],
            reported_statements=[],
            protective_factors=[],
            risk_indicators=[],
            recommended_follow_up=["Review the recording context and re-process or document manually."],
            uncertainty=["Local LLM response did not match the required schema."],
        )


def _loads_json_object(content: str) -> dict:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(cleaned[start : end + 1])
