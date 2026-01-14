"""Audio extraction utilities for embedded PPTX media."""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import List

from ..exceptions import FileOperationError

logger = logging.getLogger(__name__)

MAX_WAV_BYTES = 25 * 1024 * 1024  # 25MB Azure transcription limit (common)
DEFAULT_SEGMENT_SECONDS = 600  # 10 minutes @ 16kHz mono -> ~19.2MB per segment


def _ensure_ffmpeg_available() -> None:
    """Ensure ffmpeg is available in PATH."""
    if shutil.which("ffmpeg") is None:
        raise FileOperationError("ffmpeg is required for audio extraction but was not found in PATH.")


def _get_ffmpeg_hwaccel_flags() -> List[str]:
    """Detect available hardware acceleration and return appropriate ffmpeg flags.

    Tries to use '-hwaccel auto' if any hardware accelerators are detected.
    """
    try:
        process = subprocess.run(
            ["ffmpeg", "-hwaccels"],
            check=False,
            capture_output=True,
            text=True,
        )
        if process.returncode == 0:
            # Output format: "Hardware acceleration methods:\nvda\nvdpau\n..."
            lines = process.stdout.strip().split("\n")
            # Filter out the header line
            accels = [line.strip() for line in lines if line.strip() and ":" not in line]
            if accels:
                logger.info("ffmpeg hardware acceleration detected: %s", ", ".join(accels))
                return ["-hwaccel", "auto"]
    except Exception as exc:
        logger.debug("Failed to probe ffmpeg hardware acceleration: %s", exc)

    return []


def _run_ffmpeg(command: list[str]) -> None:
    """Run an ffmpeg command and raise with stderr on failure."""
    process = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if process.returncode != 0:
        raise FileOperationError(
            f"ffmpeg command failed: {' '.join(command)} | stderr: {process.stderr.strip()}"
        )


def _split_audio_into_segments(
    video_path: Path, output_dir: Path, base_stem: str, segment_seconds: int
) -> List[Path]:
    """Split audio into multiple WAV segments to stay under size limits."""
    output_dir.mkdir(parents=True, exist_ok=True)
    segment_pattern = output_dir / f"{base_stem}_part%03d.wav"

    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
    ]
    command.extend(_get_ffmpeg_hwaccel_flags())
    command.extend(
        [
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "segment",
            "-segment_time",
            str(segment_seconds),
            "-reset_timestamps",
            "1",
            str(segment_pattern),
        ]
    )

    _run_ffmpeg(command)
    segments = sorted(output_dir.glob(f"{base_stem}_part*.wav"))
    if not segments:
        raise FileOperationError("ffmpeg segmenting completed but no output files were produced.")
    return segments


def extract_audio_from_video(
    video_path: Path,
    out_wav_path: Path,
    *,
    max_bytes: int = MAX_WAV_BYTES,
    segment_seconds: int = DEFAULT_SEGMENT_SECONDS,
) -> List[Path]:
    """Extract mono 16k WAV audio from a video file.

    Returns a list of audio file paths. When the initial WAV exceeds the size
    guard, the function falls back to segmented WAV outputs capped by duration.
    """
    _ensure_ffmpeg_available()

    if not video_path.is_file():
        raise FileOperationError(f"Video file not found: {video_path}")

    out_wav_path.parent.mkdir(parents=True, exist_ok=True)

    base_command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
    ]
    base_command.extend(_get_ffmpeg_hwaccel_flags())
    base_command.extend(
        [
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "wav",
            str(out_wav_path),
        ]
    )

    _run_ffmpeg(base_command)

    try:
        output_size = out_wav_path.stat().st_size
    except OSError as exc:
        raise FileOperationError(f"Unable to read extracted audio size: {exc}") from exc

    if output_size <= max_bytes:
        return [out_wav_path]

    logger.info(
        "Extracted audio exceeds size limit; falling back to segmented output",
        extra={"video_path": str(video_path), "output_size": output_size, "max_bytes": max_bytes},
    )

    # Remove oversized output before segmenting to avoid confusion.
    try:
        out_wav_path.unlink(missing_ok=True)
    except OSError:
        # Non-fatal: continue to segment.
        pass

    return _split_audio_into_segments(
        video_path=video_path,
        output_dir=out_wav_path.parent,
        base_stem=out_wav_path.stem,
        segment_seconds=segment_seconds,
    )
