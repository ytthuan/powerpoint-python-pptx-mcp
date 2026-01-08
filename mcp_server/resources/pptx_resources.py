"""PPTX file resources for MCP server."""

import json
from pathlib import Path
from typing import Any, Dict, List

from mcp.types import Resource

from ..core.pptx_handler import PPTXHandler


def list_pptx_resources(base_path: str | Path = ".") -> List[Resource]:
    """List all PPTX files as resources."""
    base_path = Path(base_path)
    resources = []
    
    # Search for PPTX files
    pptx_files = list(base_path.rglob("*.pptx"))
    
    for pptx_path in pptx_files:
        try:
            handler = PPTXHandler(pptx_path)
            info = handler.get_presentation_info()
            
            resource_uri = f"pptx://{pptx_path.resolve()}"
            resources.append(
                Resource(
                    uri=resource_uri,
                    name=pptx_path.name,
                    description=f"PowerPoint presentation: {info['slide_count']} slides",
                    mimeType="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                )
            )
        except Exception:
            # Skip invalid PPTX files
            continue
    
    return resources


def get_pptx_resource(uri: str) -> Dict[str, Any]:
    """Get resource content for a PPTX file."""
    if not uri.startswith("pptx://"):
        raise ValueError(f"Invalid PPTX resource URI: {uri}")
    
    # Extract file path from URI
    file_path = uri[7:]  # Remove "pptx://" prefix
    pptx_path = Path(file_path)
    
    if not pptx_path.exists():
        raise FileNotFoundError(f"PPTX file not found: {pptx_path}")
    
    handler = PPTXHandler(pptx_path)
    info = handler.get_presentation_info()
    
    # Return metadata as JSON
    return {
        "uri": uri,
        "file_path": str(pptx_path),
        "file_name": pptx_path.name,
        "slide_count": info["slide_count"],
        "slide_size": info["slide_size"],
    }

