import logging
import shutil
import time
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.db.session import get_db
from backend.app.schemas import AiHealth, CaseCreate, CaseDetail, CaseOut, ProcessResponse
from backend.app.services.cases import append_update, create_case, get_case_detail, get_or_create_case, search_cases, to_case_out, to_update_out
from backend.app.services.ollama import check_ollama, summarise_transcript
from backend.app.services.recommendation import build_recommendation
from backend.app.services.transcription import transcribe_english

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.head("/health")
def health_head() -> None:
    return None


@router.get("/ai/health", response_model=AiHealth)
async def ai_health() -> AiHealth:
    return await check_ollama()


@router.post("/cases", response_model=CaseOut)
def create_case_route(payload: CaseCreate, db: Session = Depends(get_db)) -> CaseOut:
    return to_case_out(create_case(db, payload.user_mode))


@router.get("/cases", response_model=list[CaseOut])
def list_cases(query: Optional[str] = None, limit: int = 100, db: Session = Depends(get_db)) -> list[CaseOut]:
    return [to_case_out(case) for case in search_cases(db, query=query, limit=limit)]


@router.get("/cases/{case_id}", response_model=CaseDetail)
def get_case(case_id: str, db: Session = Depends(get_db)) -> CaseDetail:
    detail = get_case_detail(db, case_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Case not found")
    return detail


@router.post("/process-audio", response_model=ProcessResponse)
async def process_audio(
    user_mode: str = Form(...),
    case_id: Optional[str] = Form(default=None),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ProcessResponse:
    if user_mode not in {"SSSG", "CARG"}:
        raise HTTPException(status_code=400, detail="Invalid user mode")

    settings = get_settings()
    suffix = Path(audio.filename or "recording.webm").suffix or ".webm"
    temp_path = settings.temp_dir / f"{uuid4().hex}{suffix}"

    try:
        with temp_path.open("wb") as output:
            shutil.copyfileobj(audio.file, output)

        audio_size = temp_path.stat().st_size
        started_at = time.perf_counter()
        transcript = transcribe_english(temp_path)
        logger.info(
            "Transcription completed: audio_bytes=%s transcript_chars=%s duration_seconds=%.2f",
            audio_size,
            len(transcript),
            time.perf_counter() - started_at,
        )
        if not transcript.strip():
            raise HTTPException(status_code=422, detail="No English speech was detected in the recording.")

        summary_started_at = time.perf_counter()
        summary = await summarise_transcript(transcript)
        logger.info("Summary completed: duration_seconds=%.2f", time.perf_counter() - summary_started_at)
        recommendation = build_recommendation(summary, user_mode)
        case = get_or_create_case(db, case_id, user_mode)
        update = append_update(db, case, user_mode, summary, recommendation)
        return ProcessResponse(case_id=case.case_id, update=to_update_out(update))
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Audio processing failed")
        raise HTTPException(status_code=500, detail=f"Local processing failed: {exc}") from exc
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except Exception:
            logger.warning("Could not delete temporary audio file: %s", temp_path)
