"""Safe XML-based editing for PPTX files to preserve animations and transitions."""

import json
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple

from lxml import etree

from ..utils.validators import validate_pptx_path, validate_slide_number


# XML namespaces for PPTX
_REL_NS = {
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

_XML_NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}


def _notes_part_for_slide(zip_in: zipfile.ZipFile, slide_no: int) -> str | None:
    """Find the notes slide part for a given slide number."""
    rel_path = f"ppt/slides/_rels/slide{slide_no}.xml.rels"
    try:
        rel_xml = zip_in.read(rel_path)
    except KeyError:
        return None

    root = etree.fromstring(rel_xml)
    for rel in root.findall("rel:Relationship", namespaces=_REL_NS):
        if rel.get("Type") == "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide":
            target = rel.get("Target")
            if not target:
                return None
            # Typically "../notesSlides/notesSlideX.xml". Normalize to zip path.
            target = target.replace("\\", "/")
            if target.startswith("../"):
                target = target[len("../") :]
            return f"ppt/{target}"
    return None


def _set_notes_text(notes_xml: bytes, notes_text: str) -> bytes:
    """Replace the text content of the notes placeholder while preserving everything else."""
    parser = etree.XMLParser(remove_blank_text=False)
    root = etree.fromstring(notes_xml, parser)

    # Find the 'body' placeholder shape which holds the notes text.
    sp_list = root.xpath("//p:sp[p:nvSpPr/p:nvPr/p:ph[@type='body']]", namespaces=_XML_NS)
    sp = sp_list[0] if sp_list else None
    if sp is None:
        # Fallback: first shape with a text body.
        sp_list = root.xpath("//p:sp[.//a:txBody]", namespaces=_XML_NS)
        sp = sp_list[0] if sp_list else None
    if sp is None:
        return notes_xml

    # Try both namespaces - txBody can be in 'a' or 'p' namespace depending on structure
    tx_list = sp.xpath(".//p:txBody", namespaces=_XML_NS)
    if not tx_list:
        tx_list = sp.xpath(".//a:txBody", namespaces=_XML_NS)
    tx_body = tx_list[0] if tx_list else None
    if tx_body is None:
        return notes_xml

    # Keep bodyPr and lstStyle, replace only paragraphs.
    for p_el in list(tx_body.findall("a:p", namespaces=_XML_NS)):
        tx_body.remove(p_el)

    # Clean the text
    import re
    cleaned_text = notes_text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned_text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '\n', cleaned_text)
    
    lines = cleaned_text.split("\n")
    if len(lines) == 0:
        lines = [""]

    for line in lines:
        p_el = etree.Element(f"{{{_XML_NS['a']}}}p")
        r_el = etree.SubElement(p_el, f"{{{_XML_NS['a']}}}r")
        
        # Check if this line should be bold
        line_stripped = line.strip()
        is_bold = line_stripped.startswith("- Short version:") or line_stripped.startswith("- Original:")
        
        if is_bold:
            r_pr = etree.SubElement(r_el, f"{{{_XML_NS['a']}}}rPr")
            r_pr.set("b", "1")
        
        t_el = etree.SubElement(r_el, f"{{{_XML_NS['a']}}}t")
        t_el.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        clean_line = ''.join(char for char in line if ord(char) >= 32 or char in '\n\r\t')
        t_el.text = clean_line
        tx_body.append(p_el)

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=None)


def _iter_updates(payload: dict) -> List[Tuple[int, str]]:
    """Yield (slide_number, notes_text) updates from supported JSON shapes."""
    updates = []
    
    if isinstance(payload, dict) and "slides" in payload and isinstance(payload["slides"], list):
        for item in payload["slides"]:
            if not isinstance(item, dict):
                raise ValueError("Invalid JSON: slides[] items must be objects")
            slide_no = item.get("slide")
            notes = item.get("notes")
            if not isinstance(slide_no, int):
                raise ValueError("Invalid JSON: slides[] item missing integer 'slide'")
            if notes is None:
                notes = ""
            if not isinstance(notes, str):
                raise ValueError("Invalid JSON: slides[] item 'notes' must be string")
            updates.append((slide_no, notes))
        return updates

    if isinstance(payload, dict):
        for k, v in payload.items():
            try:
                slide_no = int(k)
            except Exception as e:
                raise ValueError(f"Invalid JSON mapping key (expected slide number): {k!r}") from e
            if v is None:
                v = ""
            if not isinstance(v, str):
                raise ValueError(f"Invalid JSON mapping value for slide {k!r}: must be string")
            updates.append((slide_no, v))
        return updates

    raise ValueError("Invalid JSON: expected object with 'slides' list or mapping of slide->notes")


def update_notes_safe(pptx_in: Path, updates: List[Tuple[int, str]], pptx_out: Path) -> None:
    """Update notes by editing only notesSlide XML parts inside the PPTX zip."""
    with zipfile.ZipFile(pptx_in, "r") as zin:
        notes_updates: Dict[str, bytes] = {}
        for slide_no, notes_text in updates:
            notes_part = _notes_part_for_slide(zin, slide_no)
            if not notes_part:
                continue
            original_notes_xml = zin.read(notes_part)
            notes_updates[notes_part] = _set_notes_text(original_notes_xml, notes_text)

        with zipfile.ZipFile(pptx_out, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename in notes_updates:
                    data = notes_updates[item.filename]
                zi = zipfile.ZipInfo(filename=item.filename, date_time=item.date_time)
                zi.compress_type = zipfile.ZIP_DEFLATED
                zi.external_attr = item.external_attr
                zi.comment = item.comment
                zi.extra = item.extra
                zi.internal_attr = item.internal_attr
                zi.create_system = item.create_system
                zout.writestr(zi, data)


def update_notes_safe_in_place(pptx_in: Path, updates: List[Tuple[int, str]]) -> None:
    """Safely overwrite PPTX using zip-mode notes editing."""
    pptx_in = pptx_in.resolve()
    tmp_dir = str(pptx_in.parent)
    fd, tmp_path = tempfile.mkstemp(prefix=pptx_in.stem + ".", suffix=".tmp.pptx", dir=tmp_dir)
    os.close(fd)
    tmp_file = Path(tmp_path)
    try:
        update_notes_safe(pptx_in, updates, tmp_file)
        os.replace(str(tmp_file), str(pptx_in))
    finally:
        if tmp_file.exists():
            try:
                tmp_file.unlink()
            except Exception:
                pass


