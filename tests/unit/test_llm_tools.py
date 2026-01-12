import pytest
from unittest.mock import MagicMock

from src.mcp_server.exceptions import InputTooLargeError, ValidationError
from src.mcp_server.tools import llm_tools


@pytest.mark.asyncio
async def test_handle_summarize_text_uses_create_response(monkeypatch):
    calls = {}

    def fake_create_response(prompt: str, **kwargs):
        calls["prompt"] = prompt
        calls["kwargs"] = kwargs
        return "mocked summary"

    monkeypatch.setattr(llm_tools, "create_response", fake_create_response)

    result = await llm_tools.handle_summarize_text(
        {"text": "hello world", "style": "concise", "temperature": 0.2}
    )

    assert result == {"summary": "mocked summary"}
    assert "hello world" in calls["prompt"]
    assert calls["kwargs"]["temperature"] == 0.2


@pytest.mark.asyncio
async def test_handle_translate_text_requires_language(monkeypatch):
    with pytest.raises(ValidationError):
        await llm_tools.handle_translate_text({"text": "hi there", "target_lang": ""})

    calls = {}

    def fake_create_response(prompt: str, **kwargs):
        calls["prompt"] = prompt
        return "translated text"

    monkeypatch.setattr(llm_tools, "create_response", fake_create_response)

    result = await llm_tools.handle_translate_text(
        {"text": "hi there", "target_lang": "Vietnamese", "preserve_terms": ["API"]}
    )

    assert result == {"translation": "translated text"}
    assert "hi there" in calls["prompt"]
    assert "API" in calls["prompt"]


@pytest.mark.asyncio
async def test_handle_summarize_text_enforces_length(monkeypatch):
    config = MagicMock()
    config.security.max_text_length = 5
    monkeypatch.setattr("src.mcp_server.utils.validators.get_config", lambda: config)

    with pytest.raises(InputTooLargeError):
        await llm_tools.handle_summarize_text({"text": "toolong"})


@pytest.mark.asyncio
async def test_handle_generate_slide_content_with_pptx(monkeypatch):
    calls = {}

    class DummyHandler:
        def __init__(self, pptx_path: str):
            calls["pptx_path"] = pptx_path

        async def get_slide_content(self, slide_number: int):
            calls["slide_number"] = slide_number
            return {"slide_number": slide_number, "title": "Title", "text": "Body", "shapes": []}

    def fake_generate_slide_content(slide_content: dict, **kwargs):
        calls["slide_content"] = slide_content
        calls["generate_kwargs"] = kwargs
        return "generated content"

    monkeypatch.setattr(llm_tools, "PPTXHandler", DummyHandler)
    monkeypatch.setattr(llm_tools, "generate_slide_content", fake_generate_slide_content)

    result = await llm_tools.handle_generate_slide_content(
        {"pptx_path": "demo.pptx", "slide_number": 1, "output_format": "speaker_notes"}
    )

    assert result == {
        "content": "generated content",
        "format": "speaker_notes",
        "language": "English",
    }
    assert calls["pptx_path"] == "demo.pptx"
    assert calls["slide_number"] == 1
    assert calls["generate_kwargs"]["output_format"] == "speaker_notes"


@pytest.mark.asyncio
async def test_handle_generate_slide_content_requires_source():
    with pytest.raises(ValidationError):
        await llm_tools.handle_generate_slide_content({"output_format": "json"})
