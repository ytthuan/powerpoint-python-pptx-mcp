"""Embedded video discovery utilities for PPTX files."""

from __future__ import annotations

import logging
import os
import zipfile
from pathlib import Path
from typing import Any, Dict, List
from xml.etree import ElementTree

from ..exceptions import FileOperationError
from ..utils.validators import validate_pptx_path, validate_slide_number

logger = logging.getLogger(__name__)

REL_NAMESPACE = "{http://schemas.openxmlformats.org/package/2006/relationships}"
VIDEO_REL_TYPES = {
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/video",
    "http://schemas.microsoft.com/office/2007/relationships/media",
    "http://schemas.microsoft.com/office/2011/relationships/media",
}


def _count_slides(zip_file: zipfile.ZipFile) -> int:
    """Count slides in the PPTX package."""
    return len([name for name in zip_file.namelist() if name.startswith("ppt/slides/slide")])


def _is_video_relationship(rel_type: str) -> bool:
    """Determine whether a relationship type represents embedded video/media."""
    return rel_type in VIDEO_REL_TYPES


def _resolve_target(target: str) -> str:
    """Resolve a relationship target to a PPTX zip path."""
    normalized_target = target.lstrip("/")
    # Resolve '..' components using os.path.normpath
    resolved = os.path.normpath(os.path.join("ppt/slides", normalized_target))
    # Ensure forward slashes for zip internal paths regardless of host OS
    return resolved.replace(os.sep, "/")


def _parse_relationships(rels_bytes: bytes) -> List[Dict[str, Any]]:
    """Parse relationship XML and return video relationship records."""
    relationships: List[Dict[str, Any]] = []
    root = ElementTree.fromstring(rels_bytes)

    for element in root.findall(f"{REL_NAMESPACE}Relationship"):
        rel_type = element.attrib.get("Type", "")
        target_mode = element.attrib.get("TargetMode", "").lower()
        if target_mode == "external" or not _is_video_relationship(rel_type):
            continue

        target = element.attrib.get("Target")
        if not target:
            continue

        relationships.append(
            {
                "relationship_id": element.attrib.get("Id", ""),
                "target": target,
            }
        )

    return relationships


def discover_embedded_videos(
    pptx_path: str | Path, slide_numbers: List[int]
) -> Dict[int, List[Dict[str, Any]]]:
    """Discover embedded video media for specified slides.

    Returns a mapping of slide number to a list of discovered video parts with
    resolved zip paths and metadata.
    """
    pptx_path = validate_pptx_path(pptx_path)
    results: Dict[int, List[Dict[str, Any]]] = {}

    try:
        with zipfile.ZipFile(pptx_path, "r") as zip_file:
            max_slides = _count_slides(zip_file)

            for slide_number in sorted(slide_numbers):
                validate_slide_number(slide_number, max_slides)
                rels_path = f"ppt/slides/_rels/slide{slide_number}.xml.rels"
                slide_results: List[Dict[str, Any]] = []

                if rels_path not in zip_file.namelist():
                    results[slide_number] = slide_results
                    continue

                relationships = _parse_relationships(zip_file.read(rels_path))

                for relationship in relationships:
                    zip_path = _resolve_target(relationship["target"])
                    if zip_path not in zip_file.namelist():
                        logger.debug(
                            "Embedded video target missing from PPTX",
                            extra={"slide": slide_number, "zip_path": zip_path},
                        )
                        continue

                    try:
                        media_info = zip_file.getinfo(zip_path)
                        size_bytes = media_info.file_size
                    except KeyError:
                        size_bytes = 0

                    slide_results.append(
                        {
                            "zip_path": zip_path,
                            "filename": Path(zip_path).name,
                            "size_bytes": size_bytes,
                            "relationship_id": relationship["relationship_id"],
                        }
                    )

                results[slide_number] = slide_results
    except FileOperationError:
        raise
    except Exception as exc:
        raise FileOperationError(f"Failed to discover embedded videos: {exc}") from exc

    return results
