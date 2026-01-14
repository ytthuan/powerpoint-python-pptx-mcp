import json
import zipfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.mcp_server import server
from src.mcp_server.exceptions import WorkspaceBoundaryError
from src.mcp_server.tools import transcript_tools
from src.mcp_server.tools.registry import reset_tool_registry
from src.mcp_server.utils.validators import validate_output_json_path


@pytest.fixture(autouse=True)
def reset_registry():
    reset_tool_registry()
    yield
    reset_tool_registry()


def test_validate_output_json_path_enforces_workspace(monkeypatch, tmp_path):
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()

    config = MagicMock()
    config.security.max_path_length = 4096
    config.security.allowed_extensions = {".pptx", ".pptm"}
    config.security.enforce_workspace_boundary = True
    config.security.workspace_dirs = [workspace_dir]

    monkeypatch.setattr("src.mcp_server.utils.validators.get_config", lambda: config)

    outside_path = tmp_path / "outside" / "result.json"
    outside_path.parent.mkdir()

    with pytest.raises(WorkspaceBoundaryError):
        validate_output_json_path(outside_path)

    inside_path = workspace_dir / "result.json"
    assert validate_output_json_path(inside_path) == inside_path.resolve()


@pytest.mark.asyncio
async def test_transcript_tool_not_listed_when_audio_unready(monkeypatch):
    monkeypatch.setattr(server, "_foundry_ready", False)
    monkeypatch.setattr(server, "_foundry_reason", None)
    monkeypatch.setattr(server, "_audio_ready", False)
    monkeypatch.setattr(server, "_audio_reason", None)
    monkeypatch.setattr(server, "check_foundry_readiness", lambda: (False, "skip"))
    monkeypatch.setattr(server, "check_audio_transcribe_readiness", lambda: (False, "missing"))

    server.register_all_tools()
    tools = await server.list_tools()
    assert all(tool.name != "transcribe_embedded_video_audio" for tool in tools)


@pytest.mark.asyncio
async def test_transcript_tool_listed_when_audio_ready(monkeypatch):
    monkeypatch.setattr(server, "_foundry_ready", False)
    monkeypatch.setattr(server, "_foundry_reason", None)
    monkeypatch.setattr(server, "_audio_ready", False)
    monkeypatch.setattr(server, "_audio_reason", None)
    monkeypatch.setattr(server, "check_foundry_readiness", lambda: (False, "skip"))
    monkeypatch.setattr(server, "check_audio_transcribe_readiness", lambda: (True, None))

    server.register_all_tools()
    tools = await server.list_tools()
    assert any(tool.name == "transcribe_embedded_video_audio" for tool in tools)


@pytest.mark.asyncio
async def test_handle_transcribe_embedded_video_audio_uses_mocks(tmp_path, monkeypatch):
    pptx_path = tmp_path / "demo.pptx"
    slide_rels = """<?xml version="1.0" encoding="UTF-8"?>
    <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
        <Relationship Id="rId1" Type="http://schemas.microsoft.com/office/2007/relationships/media" Target="../media/video1.mp4"/>
    </Relationships>
    """

    with zipfile.ZipFile(pptx_path, "w") as archive:
        archive.writestr("ppt/slides/slide1.xml", "<p:sld xmlns:p='http://schemas.openxmlformats.org/presentationml/2006/main'></p:sld>")  # noqa: E501
        archive.writestr("ppt/slides/_rels/slide1.xml.rels", slide_rels)
        archive.writestr("ppt/media/video1.mp4", b"video-bytes")

    def fake_extract(video_path: Path, out_wav_path: Path, **kwargs):
        out_wav_path.parent.mkdir(parents=True, exist_ok=True)
        out_wav_path.write_bytes(b"wav-bytes")
        return [out_wav_path]

    def fake_transcribe(audio_path: Path, *, language=None, prompt=None, response_format="json"):
        return {"text": f"transcript-for-{audio_path.name}", "language": language, "prompt": prompt}

    monkeypatch.setattr(transcript_tools, "extract_audio_from_video", fake_extract)
    monkeypatch.setattr(transcript_tools, "transcribe_audio_file", fake_transcribe)

    result = await transcript_tools.handle_transcribe_embedded_video_audio(
        {"pptx_path": str(pptx_path), "slide_numbers": [1], "include_raw_response": True}
    )

    assert result["success"] is True
    assert result["summary"]["videos_processed"] == 1
    assert result["summary"]["segments_transcribed"] == 1
    slide_entry = result["slides"][0]
    assert slide_entry["slide_number"] == 1
    assert slide_entry["videos"][0]["transcripts"][0]["text"].startswith("transcript-for")

    output_path = Path(result["output_json_path"])
    assert output_path.exists()
    written = json.loads(output_path.read_text())
    assert written["summary"]["videos_processed"] == 1
    assert written["slides"][0]["videos"][0]["transcripts"][0]["text"].startswith("transcript-for")
