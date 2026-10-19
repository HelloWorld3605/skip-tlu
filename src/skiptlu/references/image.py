from pathlib import Path
import hashlib

from PIL import Image

from skiptlu.references.models import DocumentImage, ParsedDocument


class ImageReferenceParser:
    def parse(self, path: Path) -> ParsedDocument:
        with Image.open(path) as image:
            width, height = image.size
            image_format = (image.format or path.suffix.lstrip(".")).lower()

        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        return ParsedDocument(
            path=path,
            file_type="image",
            images=[
                DocumentImage(
                    name=path.name,
                    path=path,
                    width=width,
                    height=height,
                )
            ],
            metadata={
                "format": image_format,
                "width": width,
                "height": height,
                "sha256": checksum,
            },
        )
