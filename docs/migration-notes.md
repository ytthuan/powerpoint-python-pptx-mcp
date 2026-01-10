# Migration Notes

## Paths changed
- Package code now lives under `src/mcp_server`.
- Integration tests moved to `tests/integration/`; unit tests remain in `tests/unit/`.
- Documentation is organized under `docs/architecture` and `docs/guides`; `AGENTS.md` remains at repo root as a top-level reference.
- Example scripts are in `examples/` and operational helpers belong in `scripts/`.

## Running the server and tools
- Install dependencies: `python3 -m pip install -r requirements.txt`
- Install the package in editable mode: `python3 -m pip install -e .`
- Run the server locally: `python3 -m mcp_server.server`

## Testing and coverage
- Test discovery uses `pythonpath = src` from `pytest.ini`.
- Run the suite: `python3 -m pytest tests/ -v`
- CI coverage uses the new source path `src/mcp_server` via pytest addopts.
