import logging
from functools import lru_cache
from pathlib import Path

from faster_whisper import WhisperModel

from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=2)
def _load_model(device: str, compute_type: str) -> WhisperModel:
    settings = get_settings()
    return WhisperModel(
        settings.whisper_model_size,
        device=device,
        compute_type=compute_type,
    )


def _transcribe_with_model(audio_path: Path, device: str, compute_type: str) -> str:
    model = _load_model(device, compute_type)
    segments, _info = model.transcribe(
        str(audio_path),
        language="en",
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=False,
    )
    return " ".join(segment.text.strip() for segment in segments if segment.text.strip())


def transcribe_english(audio_path: Path) -> str:
    settings = get_settings()
    try:
        return _transcribe_with_model(
            audio_path,
            settings.whisper_device,
            settings.whisper_compute_type,
        )
    except Exception as exc:
        if settings.whisper_device.lower() != "cuda":
            raise
        message = str(exc).lower()
        cuda_driver_error = "cuda driver version is insufficient" in message
        cuda_runtime_error = "cuda" in message and ("driver" in message or "runtime" in message)
        if not (cuda_driver_error or cuda_runtime_error):
            raise

        logger.warning(
            "CUDA transcription failed; falling back to CPU int8. Original error: %s",
            exc,
        )
        return _transcribe_with_model(audio_path, "cpu", "int8")
