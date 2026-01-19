"""Azure OpenAI audio transcription client helpers."""

from __future__ import annotations

import io
import logging
import wave
from pathlib import Path
from typing import Any, Optional, Tuple

from openai import AzureOpenAI

from ..config import get_config
from ..exceptions import FileOperationError, PPTXError

logger = logging.getLogger(__name__)

_audio_client: Optional[AzureOpenAI] = None


class AudioTranscriptionConfigError(PPTXError):
    """Raised when required audio transcription configuration is missing."""

    def __init__(self, message: str):
        super().__init__(message)


class AudioTranscriptionClientError(PPTXError):
    """Raised when audio transcription requests fail."""

    def __init__(self, message: str):
        super().__init__(message)


def _get_audio_settings() -> Tuple[Optional[str], Optional[str], str, str, Optional[str]]:
    """Fetch required audio transcription settings from configuration."""
    config = get_config()

    endpoint = config.audio_endpoint
    deployment = config.audio_deployment
    key = config.audio_key
    api_version = config.audio_api_version
    region = config.audio_region

    missing = []
    if not endpoint and not region:
        missing.append("SPEECH_ENDPOINT (or SPEECH_REGION)")
    if not key:
        missing.append("SPEECH_KEY")

    if missing:
        raise AudioTranscriptionConfigError(
            f"Missing required audio transcription configuration: {', '.join(missing)}"
        )

    return endpoint, deployment, key, api_version, region


def _build_silence_wav(duration_seconds: float = 0.25, sample_rate: int = 16000) -> io.BytesIO:
    """Create a small in-memory WAV buffer of silence for readiness checks."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)  # 16-bit samples
        wav_file.setframerate(sample_rate)
        frame_count = int(sample_rate * duration_seconds)
        wav_file.writeframes(b"\x00\x00" * frame_count)
    buffer.seek(0)
    return buffer


def get_audio_openai_client() -> AzureOpenAI:
    """Create or return cached Azure OpenAI client for audio transcription."""
    global _audio_client
    if _audio_client is not None:
        return _audio_client

    try:
        endpoint, _, key, api_version, region = _get_audio_settings()

        # If we have a region but no endpoint, construct the standard Speech endpoint
        if not endpoint and region:
            endpoint = f"https://{region}.api.cognitive.microsoft.com"

        _audio_client = AzureOpenAI(
            api_key=key,
            azure_endpoint=endpoint,
            api_version=api_version,
        )
        return _audio_client
    except PPTXError:
        raise
    except Exception as exc:
        raise AudioTranscriptionClientError(
            f"Failed to create Azure OpenAI client: {exc}. Verify SPEECH_* or AUDIO_* settings."
        ) from exc


def transcribe_audio_file(
    path: Path,
    *,
    language: Optional[str] = None,
    prompt: Optional[str] = None,
    response_format: str = "json",
) -> dict[str, Any]:
    """Transcribe an audio file using Azure OpenAI."""
    if not path.is_file():
        raise FileOperationError(f"Audio file not found: {path}")

    endpoint, deployment, _, _, _ = _get_audio_settings()
    client = get_audio_openai_client()

    try:
        with path.open("rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model=deployment,
                file=(path.name, audio_file, "application/octet-stream"),
                language=language,
                prompt=prompt,
                response_format=response_format,
            )
        if hasattr(transcription, "model_dump"):
            return transcription.model_dump()
        if hasattr(transcription, "to_dict"):
            return transcription.to_dict()
        if isinstance(transcription, dict):
            return transcription
        return {"result": str(transcription), "endpoint": endpoint}
    except PPTXError:
        raise
    except Exception as exc:
        raise AudioTranscriptionClientError(
            f"Audio transcription failed for {path}: {exc}"
        ) from exc


def check_audio_transcribe_readiness(timeout_seconds: float = 10.0) -> Tuple[bool, Optional[str]]:
    """Verify Azure OpenAI audio transcription connectivity with a minimal request."""
    try:
        endpoint, deployment, _, _, _ = _get_audio_settings()
        client = get_audio_openai_client()
    except PPTXError as exc:
        return False, str(exc)
    except Exception as exc:
        return False, f"Failed to initialize audio client: {exc}"

    silence_wav = _build_silence_wav()

    try:
        transcription = client.audio.transcriptions.create(
            model=deployment,
            file=("silence.wav", silence_wav, "audio/wav"),
            language="en",
            response_format="json",
            timeout=timeout_seconds,
        )
        if hasattr(transcription, "model_dump"):
            transcription.model_dump()
        elif hasattr(transcription, "to_dict"):
            transcription.to_dict()
        return True, None
    except Exception as exc:
        logger.error(
            "Audio transcription readiness check failed",
            extra={"endpoint": endpoint, "deployment": deployment},
            exc_info=True,
        )
        return False, f"Audio transcription readiness check failed: {exc}"


def reset_audio_client() -> None:
    """Reset cached audio client (useful for testing)."""
    global _audio_client
    _audio_client = None
