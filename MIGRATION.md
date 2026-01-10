# Migration Guide: Scripts to MCP Tools

This guide helps you migrate from the deprecated scripts to the MCP (Model Context Protocol) server tools.

## Overview

The `scripts/` directory contains deprecated CLI scripts that are being phased out in favor of the MCP server tools. The MCP server provides:

- ✅ **Better error handling** with structured exceptions
- ✅ **Enhanced security** with input validation and workspace boundaries
- ✅ **Consistent API** across all operations
- ✅ **Type safety** with comprehensive type hints
- ✅ **Logging & monitoring** with correlation IDs
- ✅ **Better testing** with >85% code coverage target

## Deprecation Timeline

| Version | Status | Action |
|---------|--------|--------|
| Current | **Deprecated** | Scripts show warnings but still work |
| Next Minor | **Removal Warning** | Scripts will show error messages |
| Next Major | **Removed** | Scripts will be completely removed |

## Migration Path

### 1. From `pptx_notes.py dump` to MCP Tools

**Old way (deprecated):**
```bash
python3 scripts/pptx_notes.py dump presentation.pptx --out notes.json
```

**New way (recommended):**
```python
# Using MCP server tools programmatically
from mcp_server.tools.notes_tools import handle_read_notes_batch

result = await handle_read_notes_batch({
    "pptx_path": "presentation.pptx",
    "slide_range": "1-100"  # or specific range
})

# Save to JSON
import json
with open("notes.json", "w") as f:
    json.dump(result, f, indent=2)
```

**Or via MCP client:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "read_notes_batch",
    "arguments": {
      "pptx_path": "presentation.pptx",
      "slide_range": "1-100"
    }
  }
}
```

### 2. From `pptx_notes.py apply` to MCP Tools

**Old way (deprecated):**
```bash
python3 scripts/pptx_notes.py apply presentation.pptx updates.json --engine zip --in-place
```

**New way (recommended):**
```python
# Using MCP server tools programmatically
from mcp_server.tools.notes_tools import handle_update_notes_batch
import json

# Load updates
with open("updates.json") as f:
    updates = json.load(f)

# Apply updates
result = await handle_update_notes_batch({
    "pptx_path": "presentation.pptx",
    "updates": updates["slides"],  # Assumes format: {"slides": [{"slide": 1, "notes": "..."}]}
    "output_path": "presentation.pptx"  # In-place update
})
```

**Or via MCP client:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "update_notes_batch",
    "arguments": {
      "pptx_path": "presentation.pptx",
      "updates": [...],
      "output_path": "presentation.pptx"
    }
  }
}
```

### 3. From `update_notes_format.py` to MCP Workflow

**Old way (deprecated):**
```bash
python3 scripts/update_notes_format.py \
    --input notes.json \
    --pptx presentation.pptx \
    --output-language vietnamese \
    --batch-size 5
```

**New way (recommended):**
```python
# Using MCP server notes workflow
from mcp_server.tools.notes_tools import handle_process_notes_workflow

result = await handle_process_notes_workflow({
    "pptx_path": "presentation.pptx",
    "output_language": "vietnamese",
    "include_translation": True,
    "include_summary": True,
    "slide_range": "1-100",  # Optional: specific slides
    "output_path": "presentation_updated.pptx"
})
```

**Or via MCP client:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "process_notes_workflow",
    "arguments": {
      "pptx_path": "presentation.pptx",
      "output_language": "vietnamese",
      "include_translation": true,
      "include_summary": true,
      "output_path": "presentation_updated.pptx"
    }
  }
}
```

## Feature Mapping

### Script Features → MCP Tools

| Script Feature | MCP Tool/Method | Notes |
|----------------|-----------------|-------|
| `dump` notes | `read_notes` or `read_notes_batch` | Single or batch read |
| `apply` with zip engine | `update_notes_batch` | Safe in-place updates |
| `apply` with python-pptx | `update_notes` | Full rewrite (use cautiously) |
| Parallel processing | Built-in to `process_notes_workflow` | Automatic parallelization |
| Status tracking | Built-in to workflows | Automatic progress tracking |
| Resume capability | Planned for workflows | Coming in next version |
| Dry-run mode | `dry_run` parameter | Available on all write operations |

## Configuration Migration

### Environment Variables

**Scripts used:**
```bash
AZURE_AI_PROJECT_ENDPOINT=https://...
MODEL_DEPLOYMENT_NAME=gpt-4
```

**MCP Server uses the same, plus:**
```bash
# Performance & caching
MCP_ENABLE_CACHE=true
MCP_CACHE_SIZE=100

# Security
MCP_MAX_FILE_SIZE=104857600  # 100MB in bytes
MCP_WORKSPACE_DIRS=/path/to/allowed,/path/to/another
MCP_ENFORCE_WORKSPACE_BOUNDARY=true

# Logging
MCP_LOG_LEVEL=INFO
MCP_LOG_FILE=/path/to/logfile.log

# Environment
MCP_ENV=production  # or development, staging
```

See `mcp_server/config.py` for full configuration options.

## API Changes

### Error Handling

**Scripts:**
```python
try:
    result = apply_notes_in_place(pptx, updates)
except Exception as e:
    print(f"Error: {e}")
```

**MCP Tools:**
```python
from mcp_server.exceptions import (
    PPTXError,
    PPTXFileNotFoundError,
    ValidationError,
    SlideNotFoundError
)

try:
    result = await handle_update_notes(args)
except PPTXFileNotFoundError as e:
    # File doesn't exist
    print(f"File not found: {e.message}")
except ValidationError as e:
    # Invalid input
    print(f"Validation error: {e.message}, details: {e.details}")
except SlideNotFoundError as e:
    # Slide doesn't exist
    print(f"Slide not found: {e.details['slide_number']}")
except PPTXError as e:
    # Any other PPTX-related error
    print(f"Error: {e.message}")
    print(f"Details: {e.to_dict()}")
```

### Return Values

**Scripts** return mixed formats (sometimes dicts, sometimes None, error handling via exceptions).

**MCP Tools** return consistent structured responses:
```python
{
    "success": true,
    "data": { ... },  # Operation-specific data
    "message": "Operation completed successfully",
    "metadata": {
        "operation": "update_notes",
        "duration_ms": 150,
        "timestamp": "2024-01-10T00:00:00Z"
    }
}
```

Or on error:
```python
{
    "success": false,
    "error": {
        "type": "ValidationError",
        "message": "Invalid slide number",
        "details": { ... }
    }
}
```

## Testing Your Migration

### 1. Test with Dry Run

Before making actual changes, test with dry-run mode:

```python
result = await handle_update_notes_batch({
    "pptx_path": "presentation.pptx",
    "updates": updates,
    "output_path": "presentation.pptx",
    "dry_run": True  # ← Won't actually modify the file
})

print(f"Would update {len(result['data']['updated_slides'])} slides")
```

### 2. Compare Outputs

Process the same file with both old and new methods and compare:

```bash
# Old method
python3 scripts/pptx_notes.py dump old_output.pptx > old.json

# New method (after processing with MCP tools)
python3 scripts/pptx_notes.py dump new_output.pptx > new.json

# Compare
diff old.json new.json
```

### 3. Validate Results

```python
# Read back and validate
result = await handle_read_notes_batch({
    "pptx_path": "updated_presentation.pptx",
    "slide_range": "1-100"
})

# Check all slides were updated
for slide_notes in result["data"]["notes"]:
    assert slide_notes["notes_text"]  # Has content
    assert "- Short version:" in slide_notes["notes_text"]  # Has format
    assert "- Original:" in slide_notes["notes_text"]
```

## Common Issues & Solutions

### Issue: "Workspace boundary error"

**Cause:** MCP server enforces workspace boundaries for security.

**Solution:** Configure workspace directories:
```bash
export MCP_WORKSPACE_DIRS="/path/to/your/presentations"
```

Or disable enforcement (not recommended for production):
```bash
export MCP_ENFORCE_WORKSPACE_BOUNDARY=false
```

### Issue: "File too large error"

**Cause:** File exceeds default 100MB limit.

**Solution:** Increase limit:
```bash
export MCP_MAX_FILE_SIZE=209715200  # 200MB in bytes
```

### Issue: "Missing Azure credentials"

**Cause:** Azure authentication not configured.

**Solution:** Same as before, use Azure CLI login or environment variables:
```bash
az login
# or
export AZURE_TENANT_ID=...
export AZURE_CLIENT_ID=...
export AZURE_CLIENT_SECRET=...
```

### Issue: "Cache-related errors"

**Cause:** Stale cache entries.

**Solution:** Clear cache or disable:
```bash
export MCP_ENABLE_CACHE=false
```

## Getting Help

### Documentation
- **README.md**: MCP server overview and setup
- **AGENTS.md**: Agent-specific instructions and guidelines
- **MCP_AGENT_INSTRUCTIONS.md**: Detailed MCP usage instructions
- **API Documentation**: See `mcp_server/` module docstrings

### Support Channels
- GitHub Issues: Report bugs or request features
- Discussions: Ask questions and share experiences

### Reporting Issues

If you encounter migration issues:

1. Check this guide and other documentation first
2. Search existing GitHub issues
3. Create a new issue with:
   - Script command you were using
   - Expected behavior
   - Actual behavior with MCP tools
   - Error messages (if any)
   - Environment details (Python version, OS, etc.)

## Checklist

Use this checklist to track your migration progress:

- [ ] Inventory all script usage in your codebase/workflows
- [ ] Review this migration guide
- [ ] Set up MCP server configuration (environment variables)
- [ ] Test MCP tools with dry-run mode
- [ ] Update automation scripts/CI pipelines
- [ ] Update documentation referencing old scripts
- [ ] Test thoroughly in development environment
- [ ] Deploy to staging and validate
- [ ] Deploy to production
- [ ] Remove deprecated script references
- [ ] Monitor for any issues

## Timeline

**Immediate (Now):**
- Start using MCP tools for new projects
- Begin planning migration for existing projects

**Next 3 Months:**
- Complete migration of all automation scripts
- Update all documentation
- Train team members on MCP tools

**After Next Major Release:**
- Scripts will be completely removed
- Only MCP tools will be supported

---

**Questions?** Open an issue on GitHub or check the documentation.

**Last Updated:** 2026-01-10
