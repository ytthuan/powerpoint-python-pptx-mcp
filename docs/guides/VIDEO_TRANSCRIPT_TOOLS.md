# Embedded Video Transcript Tools Implementation Log

## Step 1: Add audio config fields/env validation — Done
- Added audio transcription configuration fields (endpoint, deployment, key, API version, and region) loaded from env with support for `SPEECH_*` aliases.
- Relaxed endpoint validation to support Azure AI Foundry unified endpoints (any secure HTTPS URL).
- Added support for `SPEECH_REGION` with automatic endpoint construction.

## Step 2: Implement audio transcribe client readiness check — Done
- Added Azure OpenAI audio client helpers with cached client creation, transcript call, and reset helper.
- Implemented readiness check using a tiny in-memory silence WAV with strict timeout and structured error logging.

## Step 3: PPTX embedded video discovery (zip-based) — Pending
## Step 3: PPTX embedded video discovery (zip-based) — Done
- Added zip-based slide relationship parser to resolve embedded video media targets per slide with size metadata.
- Skips external targets and logs missing media entries without stopping discovery.

## Step 4: Audio extraction via ffmpeg — Pending
## Step 4: Audio extraction via ffmpeg — Done
- Added ffmpeg-powered audio extraction producing mono 16k WAV with explicit error surfacing.
- Introduced deterministic fallback to segmented WAV outputs when size exceeds Azure limits.
- Added hardware acceleration detection (`-hwaccel auto`) to improve processing speed on supported systems.

## Step 5: New MCP tool: transcribe embedded video audio — Pending
## Step 5: New MCP tool: transcribe embedded video audio — Done
- Added async MCP tool to extract embedded videos per slide, run ffmpeg audio extraction, transcribe via Azure, and emit per-slide JSON with summaries.
- Validates slide inputs, output JSON path, optional language/prompt, and preserves per-slide error reporting without stopping the batch.

## Step 6: Gate tool registration/listing on startup connection check — Pending
## Step 6: Gate tool registration/listing on startup connection check — Done
- Added audio readiness gating with a real Azure transcription probe to control registration and listing of transcript tools.
- Mirrors Foundry gating with a single informative log line when audio tools are skipped.

## Step 7: Docker + runtime dependency for ffmpeg — Pending
## Step 7: Docker + runtime dependency for ffmpeg — Done
- Added ffmpeg to the slim-based Docker image so transcription tooling works in containers.
- Kept existing build dependencies intact while cleaning apt caches.

## Step 8: Tests — Pending
## Step 8: Tests — Done
- Added unit tests covering embedded video discovery (skips external targets), output JSON path validation, and mocked transcription workflow.
- Added server gating tests ensuring transcript tool listing aligns with audio readiness checks.

## Step 9: Implementation log doc — Done
- Recorded per-step completion notes for audio config, readiness, extractors, tooling, Docker, and tests.
- Documented gating behavior and batch error-handling expectations for transcript tools.
