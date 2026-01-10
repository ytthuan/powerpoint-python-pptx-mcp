import pytest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from lxml import etree
from src.mcp_server.core.safe_editor import (
    _notes_part_for_slide,
    _set_notes_text,
    _iter_updates,
    update_notes_safe,
    update_notes_safe_in_place,
    _XML_NS,
)


def test_iter_updates_slides_list():
    payload = {"slides": [{"slide": 1, "notes": "note 1"}, {"slide": 2, "notes": "note 2"}]}
    expected = [(1, "note 1"), (2, "note 2")]
    assert _iter_updates(payload) == expected


def test_iter_updates_mapping():
    payload = {"1": "note 1", "2": "note 2"}
    expected = [(1, "note 1"), (2, "note 2")]
    assert _iter_updates(payload) == expected


def test_iter_updates_invalid_payload():
    with pytest.raises(ValueError, match="Invalid JSON"):
        _iter_updates([1, 2, 3])


def test_iter_updates_invalid_slide_no():
    payload = {"abc": "note"}
    with pytest.raises(ValueError, match="Invalid JSON mapping key"):
        _iter_updates(payload)


def test_set_notes_text_basic():
    notes_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <p:notes xmlns:a="{_XML_NS['a']}" xmlns:p="{_XML_NS['p']}">
        <p:sp>
            <p:nvSpPr><p:nvPr><p:ph type="body"/></p:nvPr></p:nvSpPr>
            <p:txBody>
                <a:bodyPr/>
                <a:p><a:r><a:t>Original Note</a:t></a:r></a:p>
            </p:txBody>
        </p:sp>
    </p:notes>
    """.encode()

    new_text = "New Note\nSecond Line"
    updated_xml = _set_notes_text(notes_xml, new_text)

    root = etree.fromstring(updated_xml)
    paragraphs = root.xpath("//a:p", namespaces=_XML_NS)
    assert len(paragraphs) == 2
    assert paragraphs[0].find(".//a:t", namespaces=_XML_NS).text == "New Note"
    assert paragraphs[1].find(".//a:t", namespaces=_XML_NS).text == "Second Line"


def test_set_notes_text_bold_formatting():
    notes_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <p:notes xmlns:a="{_XML_NS['a']}" xmlns:p="{_XML_NS['p']}">
        <p:sp>
            <p:nvSpPr><p:nvPr><p:ph type="body"/></p:nvPr></p:nvSpPr>
            <p:txBody><a:p><a:r><a:t>X</a:t></a:r></a:p></p:txBody>
        </p:sp>
    </p:notes>
    """.encode()

    new_text = "- Short version: Summary\n- Original: Full content"
    updated_xml = _set_notes_text(notes_xml, new_text)

    root = etree.fromstring(updated_xml)
    runs = root.xpath("//a:r", namespaces=_XML_NS)
    assert len(runs) == 2
    # Check for bold property <a:rPr b="1"/>
    assert runs[0].find("a:rPr", namespaces=_XML_NS).get("b") == "1"
    assert runs[1].find("a:rPr", namespaces=_XML_NS).get("b") == "1"


def test_notes_part_for_slide_found():
    # Create a mock zip with a .rels file
    rels_content = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '    <Relationships xmlns="http://schemas.openxmlformats.org/'
        'package/2006/relationships">\n'
        '        <Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
        'notesSlide" Target="../notesSlides/notesSlide1.xml"/>\n'
        "    </Relationships>\n"
        "    "
    ).encode()

    mock_zip = MagicMock(spec=zipfile.ZipFile)
    mock_zip.read.return_value = rels_content

    part = _notes_part_for_slide(mock_zip, 1)
    assert part == "ppt/notesSlides/notesSlide1.xml"


def test_notes_part_for_slide_not_found():
    mock_zip = MagicMock(spec=zipfile.ZipFile)
    mock_zip.read.side_effect = KeyError()

    part = _notes_part_for_slide(mock_zip, 1)
    assert part is None


@patch("zipfile.ZipFile")
def test_update_notes_safe(mock_zip_class):
    mock_zin = MagicMock()
    mock_zout = MagicMock()

    # Use context manager
    mock_zin.__enter__.return_value = mock_zin
    mock_zout.__enter__.return_value = mock_zout

    # Configure mock_zip_class
    def zip_side_effect(file, mode, **kwargs):
        if mode == "r":
            return mock_zin
        if mode == "w":
            return mock_zout
        return MagicMock()

    mock_zip_class.side_effect = zip_side_effect

    # Setup zin.infolist and zin.read
    item = MagicMock()
    item.filename = "ppt/slides/slide1.xml"
    item.date_time = (2024, 1, 1, 0, 0, 0)
    item.external_attr = 0
    item.comment = b""
    item.extra = b""
    item.internal_attr = 0
    item.create_system = 0
    mock_zin.infolist.return_value = [item]
    mock_zin.read.return_value = b"some content"

    # No updates for this slide found in _notes_part_for_slide, should just copy
    with patch("src.mcp_server.core.safe_editor._notes_part_for_slide", return_value=None):
        update_notes_safe(Path("in.pptx"), [(1, "new note")], Path("out.pptx"))

    # Check if zout.writestr was called to copy the slide
    mock_zout.writestr.assert_called()


@patch("src.mcp_server.core.safe_editor.update_notes_safe")
@patch("os.replace")
def test_update_notes_safe_in_place(mock_replace, mock_update_safe):
    with patch("tempfile.mkstemp", return_value=(999, "/tmp/tmp.pptx")), patch("os.close"):

        path = Path("/tmp/test.pptx")
        update_notes_safe_in_place(path, [(1, "note")])

        mock_update_safe.assert_called_once()
        mock_replace.assert_called_once()
