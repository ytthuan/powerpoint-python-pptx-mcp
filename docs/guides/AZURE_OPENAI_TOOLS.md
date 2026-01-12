# Azure OpenAI (Foundry) Tools Implementation Log

## Step 1: Review legacy Foundry helpers — Done
- Reviewed legacy Foundry client, prompts, and slide generation helpers under `will-be-remove-after-in-coporate`.
- Noted response extraction approach, prompt tone rules (including Vietnamese guidance), and metadata normalization needs for reuse.

## Step 2: Implement LLM client/prompts/slide generation modules — Done
- Added cached Foundry client wrapper with readiness check, response extraction, and configuration guards for endpoint/model.
- Built prompt templates and slide metadata normalization aligned with PPTXHandler shapes for generation outputs.

## Step 3: Create LLM MCP tools with validation paths — Done
- Added summarize, translate, and slide generation tools with input schemas, validation for text/parameters, and optional temperature/token controls.
- Wired handlers to reuse Foundry prompts/helpers and PPTXHandler-driven slide content retrieval when metadata is not supplied.

## Step 4: Wire conditional registration/listing in server — Done
- Added Foundry readiness check gating registration/listing of LLM tools, with single log line when skipped.
- Included handlers in tool registry only when Azure configuration and client initialization succeed.

## Step 5: Add tests covering handlers and validation — Done
- Added unit tests with monkeypatched Foundry calls to assert summarize/translate/generate handlers return mocked outputs and enforce language/metadata requirements.
- Covered validation errors for oversized text and missing slide content inputs without hitting real Azure services.

## Step 6: Write implementation log and update AI_AGENT_GUIDE — Done
- Logged per-step completion and updated AI agent guide with Foundry LLM tools, example usage, and configuration requirements.
- Documented env vars `AZURE_AI_PROJECT_ENDPOINT` and `MODEL_DEPLOYMENT_NAME` plus DefaultAzureCredential expectation and conditional tool availability.

## Step 7: Delete will-be-remove-after-in-coporate folder — Done
- Removed legacy Foundry helper folder now superseded by native LLM modules under `src/mcp_server/llm`.
- Confirmed no remaining dependencies on the deprecated path to avoid accidental imports.
