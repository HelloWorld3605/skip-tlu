from pathlib import Path

from PIL import Image

from skiptlu.references.image import ImageReferenceParser


def test_image_reference_parser_extracts_dimensions_and_checksum(tmp_path):
    path = tmp_path / "picture.jpg"
    Image.new("RGB", (320, 180)).save(path)

    parsed = ImageReferenceParser().parse(path)

    assert parsed.file_type == "image"
    assert parsed.images[0].width == 320
    assert parsed.images[0].height == 180
    assert len(parsed.metadata["sha256"]) == 64
