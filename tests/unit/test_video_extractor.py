import zipfile

from src.mcp_server.core.video_extractor import discover_embedded_videos


def test_discover_embedded_videos_skips_external_targets(tmp_path):
    pptx_path = tmp_path / "video_demo.pptx"
    slide_rels = (
        """<?xml version="1.0" encoding="UTF-8"?>
    <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
        <Relationship Id="rId1" """
        """Type="http://schemas.microsoft.com/office/2007/relationships/media" """
        """Target="../media/video1.mp4"/>
        <Relationship Id="rId2" """
        """Type="http://schemas.microsoft.com/office/2007/relationships/media" """
        """Target="http://example.com/video.mp4" TargetMode="External"/>
        <Relationship Id="rId3" """
        """Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" """
        """Target="../media/image1.png"/>
    </Relationships>
    """
    )

    with zipfile.ZipFile(pptx_path, "w") as archive:
        archive.writestr(
            "ppt/slides/slide1.xml",
            "<p:sld xmlns:p='http://schemas.openxmlformats.org/presentationml/2006/main'></p:sld>",
        )  # noqa: E501
        archive.writestr("ppt/slides/_rels/slide1.xml.rels", slide_rels)
        archive.writestr("ppt/media/video1.mp4", b"video-bytes")

    result = discover_embedded_videos(pptx_path, [1])

    assert 1 in result
    assert len(result[1]) == 1
    video_entry = result[1][0]
    assert video_entry["zip_path"] == "ppt/media/video1.mp4"
    assert video_entry["filename"] == "video1.mp4"
    assert video_entry["relationship_id"] == "rId1"
    assert video_entry["size_bytes"] == len(b"video-bytes")
