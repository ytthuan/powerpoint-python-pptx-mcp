"""Azure AI Foundry client helpers with cached OpenAI client access."""

from __future__ import annotations

import logging
from typing import Optional, Tuple

from azure.ai.projects import AIProjectClient
from azure.core.exceptions import HttpResponseError
from azure.identity import DefaultAzureCredential

from ..config import get_config
from ..exceptions import PPTXError

logger = logging.getLogger(__name__)

_project_client: Optional[AIProjectClient] = None
_openai_client = None


class FoundryConfigurationError(PPTXError):
    """Raised when required Foundry configuration is missing."""

    def __init__(self, message: str):
        super().__init__(message)


class FoundryClientError(PPTXError):
    """Raised when Foundry client operations fail."""

    def __init__(self, message: str):
        super().__init__(message)


def _get_foundry_settings() -> Tuple[str, str]:
    """Fetch required Foundry settings from configuration."""
    config = get_config()
    endpoint = config.azure_endpoint
    model_name = config.azure_deployment_name

    missing = []
    if not endpoint:
        missing.append("AZURE_AI_PROJECT_ENDPOINT")
    if not model_name:
        missing.append("MODEL_DEPLOYMENT_NAME")

    if missing:
        raise FoundryConfigurationError(
            f"Missing required Foundry configuration: {', '.join(missing)}"
        )

    return endpoint, model_name


def get_ai_project_client() -> AIProjectClient:
    """Create or return cached AIProjectClient."""
    global _project_client
    if _project_client is not None:
        return _project_client

    try:
        endpoint, _ = _get_foundry_settings()
        credential = DefaultAzureCredential()
        _project_client = AIProjectClient(endpoint=endpoint, credential=credential)
        return _project_client
    except PPTXError:
        raise
    except Exception as exc:
        raise FoundryClientError(
            f"Failed to create AIProjectClient: {exc}. Verify Azure credentials and endpoint."
        ) from exc


def get_openai_client():
    """Create or return cached OpenAI client from AIProjectClient."""
    global _openai_client
    if _openai_client is not None:
        return _openai_client

    try:
        project_client = get_ai_project_client()
        _openai_client = project_client.get_openai_client()
        return _openai_client
    except PPTXError:
        raise
    except Exception as exc:
        raise FoundryClientError(
            f"Failed to get OpenAI client from AIProjectClient: {exc}."
        ) from exc


def create_response(
    input_text: str,
    *,
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_output_tokens: Optional[int] = None,
) -> str:
    """Create a text response using the Foundry Models Responses API."""
    try:
        _, model_name = _get_foundry_settings()
        openai_client = get_openai_client()

        if system_prompt:
            input_data = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text},
            ]
        else:
            input_data = input_text

        params = {
            "model": model_name,
            "input": input_data,
        }

        if temperature is not None:
            params["temperature"] = temperature
        if max_output_tokens is not None:
            params["max_output_tokens"] = max_output_tokens

        response = openai_client.responses.create(**params)
        return _extract_response_text(response)
    except HttpResponseError as exc:
        raise FoundryClientError(
            f"HTTP error from Foundry API: {exc}. Check endpoint, model deployment, and credentials."
        ) from exc
    except PPTXError:
        raise
    except Exception as exc:
        raise FoundryClientError(f"Unexpected error calling Foundry API: {exc}") from exc


def _extract_response_text(response: object) -> str:
    """Extract text content from a Foundry response object."""
    if hasattr(response, "output_text"):
        return response.output_text

    if hasattr(response, "output") and isinstance(response.output, list):
        if len(response.output) > 0:
            first_item = response.output[0]
            if hasattr(first_item, "content"):
                content = first_item.content
                if isinstance(content, list) and content:
                    first_content = content[0]
                    if hasattr(first_content, "text"):
                        return first_content.text
        return str(response.output)

    return str(response)


def check_foundry_readiness() -> Tuple[bool, Optional[str]]:
    """Check whether Foundry dependencies and configuration are ready for use."""
    try:
        _get_foundry_settings()
        get_ai_project_client()
        get_openai_client()
        return True, None
    except PPTXError as exc:
        return False, str(exc)
    except Exception as exc:
        return False, f"Failed to initialize Foundry client: {exc}"


def reset_foundry_clients() -> None:
    """Reset cached Foundry clients (useful for testing)."""
    global _project_client, _openai_client
    _project_client = None
    _openai_client = None
