---
applyTo: "src/mcp_server/core/**/*.py"
excludeAgent: "documentation-writer"
---

# Core Services Development

These instructions apply to core service implementations in `src/mcp_server/core/`.

## Core services overview

Core services provide the fundamental PPTX manipulation capabilities. They must be:
- **Reliable**: No data loss, no corruption
- **Safe**: Validate all inputs, handle all errors
- **Efficient**: Use caching, lazy loading
- **Maintainable**: Clear abstractions, well-tested

## Critical requirements

- **Never modify PPTX structure accidentally** - Preserve animations, transitions, layouts
- **Always validate file integrity** - Check PPTX is valid before and after operations
- **Use context managers** - Properly close file handles
- **Handle encoding carefully** - Support Unicode (especially Vietnamese characters)
- **Log all operations** - Structured logging with context

## PPTX Handler pattern

```python
from typing import Optional, List, Dict, Any
from pptx import Presentation
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class PPTXHandler:
    """Handle PPTX file operations safely and efficiently."""
    
    def __init__(self, cache_size: int = 100):
        """Initialize handler with optional caching.
        
        Args:
            cache_size: Maximum number of presentations to cache
        """
        self._cache = LRUCache(cache_size)
        
    async def read_presentation(
        self,
        pptx_path: str,
        use_cache: bool = True
    ) -> Presentation:
        """Read presentation from file with optional caching.
        
        Args:
            pptx_path: Path to PPTX file
            use_cache: Whether to use cache
            
        Returns:
            Presentation object
            
        Raises:
            FileOperationError: If file cannot be read
        """
        try:
            # Check cache first
            if use_cache and pptx_path in self._cache:
                logger.debug(f"Cache hit for {pptx_path}")
                return self._cache[pptx_path]
            
            # Validate file exists and is readable
            path = Path(pptx_path)
            if not path.exists():
                raise FileOperationError(f"File not found: {pptx_path}")
            
            # Load presentation
            logger.info(f"Loading presentation: {pptx_path}")
            prs = Presentation(pptx_path)
            
            # Cache if requested
            if use_cache:
                self._cache[pptx_path] = prs
                
            return prs
            
        except Exception as e:
            logger.error(f"Failed to read presentation: {e}", exc_info=True)
            raise FileOperationError(f"Cannot read PPTX: {e}")
```

## Safe file operations

Always use safe patterns for file operations:

```python
from tempfile import NamedTemporaryFile
from shutil import copy2
from pathlib import Path

async def save_presentation_safe(
    prs: Presentation,
    output_path: str,
    create_backup: bool = True
) -> None:
    """Save presentation safely with optional backup.
    
    Args:
        prs: Presentation to save
        output_path: Destination path
        create_backup: Whether to create backup of existing file
        
    Raises:
        FileOperationError: If save fails
    """
    try:
        output = Path(output_path)
        
        # Create backup if file exists
        if create_backup and output.exists():
            backup_path = output.with_suffix(output.suffix + ".backup")
            copy2(output, backup_path)
            logger.info(f"Created backup: {backup_path}")
        
        # Save to temporary file first
        with NamedTemporaryFile(
            mode='wb',
            delete=False,
            suffix='.pptx'
        ) as tmp_file:
            tmp_path = Path(tmp_file.name)
            prs.save(tmp_file.name)
            
        # Move temp file to final destination (atomic on same filesystem)
        tmp_path.replace(output)
        logger.info(f"Saved presentation: {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to save presentation: {e}", exc_info=True)
        raise FileOperationError(f"Cannot save PPTX: {e}")
```

## Zip-based editing for notes

For speaker notes, prefer zip-based editing to preserve animations:

```python
import zipfile
from lxml import etree
from io import BytesIO

async def update_notes_zip(
    pptx_path: str,
    slide_number: int,
    notes_text: str
) -> None:
    """Update notes using zip-based editing (preserves animations).
    
    Args:
        pptx_path: Path to PPTX file
        slide_number: Slide number (1-indexed)
        notes_text: New notes text
        
    Raises:
        FileOperationError: If update fails
    """
    try:
        # Read PPTX as zip
        with zipfile.ZipFile(pptx_path, 'r') as zip_in:
            # Get notes slide XML
            notes_path = f'ppt/notesSlides/notesSlide{slide_number}.xml'
            
            if notes_path not in zip_in.namelist():
                raise FileOperationError(f"Notes slide {slide_number} not found")
            
            # Parse XML
            notes_xml = zip_in.read(notes_path)
            root = etree.fromstring(notes_xml)
            
            # Update text content (preserve structure)
            # ... XML manipulation ...
            
            # Write back to zip
            with zipfile.ZipFile(pptx_path + '.tmp', 'w') as zip_out:
                for item in zip_in.namelist():
                    if item == notes_path:
                        # Write updated notes
                        zip_out.writestr(item, etree.tostring(root))
                    else:
                        # Copy unchanged
                        zip_out.writestr(item, zip_in.read(item))
        
        # Replace original (atomic)
        Path(pptx_path + '.tmp').replace(pptx_path)
        
    except Exception as e:
        logger.error(f"Zip-based update failed: {e}", exc_info=True)
        raise FileOperationError(f"Cannot update notes: {e}")
```

## Error handling

Use specific exceptions:

```python
from mcp_server.exceptions import (
    FileOperationError,
    ValidationError,
    PPTXCorruptError
)

# Validation errors
if not Path(pptx_path).exists():
    raise FileOperationError(f"File not found: {pptx_path}")

# Corruption errors
try:
    prs = Presentation(pptx_path)
except Exception as e:
    raise PPTXCorruptError(f"Corrupted PPTX: {e}")

# General operation errors
try:
    # operation
except Exception as e:
    raise FileOperationError(f"Operation failed: {e}")
```

## Memory management

Handle large files carefully:

```python
# Manage Presentation lifetime explicitly (no context manager support)
prs = Presentation(pptx_path)
# Work with presentation
pass
# Release reference when done
prs = None

# Clear cache when needed
self._cache.clear()

# Use generators for large data
def iter_slides(prs: Presentation):
    """Iterate slides without loading all at once."""
    for slide in prs.slides:
        yield slide

# Limit cache size
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_data(key: str):
    # Expensive operation
    pass
```

## Testing core services

```python
@pytest.mark.unit
async def test_read_presentation_success(sample_pptx):
    """Test reading valid presentation."""
    handler = PPTXHandler()
    prs = await handler.read_presentation(sample_pptx)
    assert prs is not None
    assert len(prs.slides) > 0

@pytest.mark.unit
async def test_read_presentation_invalid_file():
    """Test error on invalid file."""
    handler = PPTXHandler()
    with pytest.raises(FileOperationError):
        await handler.read_presentation("nonexistent.pptx")

@pytest.mark.integration
async def test_save_creates_backup(tmp_path, sample_pptx):
    """Test backup creation on save."""
    output = tmp_path / "output.pptx"
    # Create existing file
    output.write_bytes(b"existing")
    
    prs = Presentation(sample_pptx)
    await save_presentation_safe(prs, str(output), create_backup=True)
    
    backup = output.with_suffix(output.suffix + ".backup")
    assert backup.exists()
```

## Performance optimization

```python
# Lazy loading
@property
def slides_count(self) -> int:
    """Get slide count without full load."""
    # Use lightweight XML parsing
    pass

# Batch operations
async def update_multiple_notes(
    pptx_path: str,
    updates: List[Dict[str, Any]]
) -> None:
    """Update multiple notes in single transaction."""
    # Open once, update all, save once
    pass

# Async I/O
import aiofiles

async def read_file_async(path: str) -> bytes:
    """Read file asynchronously."""
    async with aiofiles.open(path, 'rb') as f:
        return await f.read()
```
