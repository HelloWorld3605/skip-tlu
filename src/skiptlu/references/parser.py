from pathlib import Path

from skiptlu.references.docx import DocxReferenceParser
from skiptlu.references.image import ImageReferenceParser
from skiptlu.references.models import ParsedDocument
from skiptlu.references.pdf import PdfReferenceParser


class ReferenceParser:
    def __init__(self) -> None:
        self._docx = DocxReferenceParser()
        self._pdf = PdfReferenceParser()
        self._image = ImageReferenceParser()

    def parse(self, path: Path) -> ParsedDocument:
        suffix = path.suffix.lower()
        if suffix == ".docx":
            return self._docx.parse(path)
        if suffix == ".pdf":
            return self._pdf.parse(path)
        if suffix in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
            return self._image.parse(path)
        raise ValueError(f"Unsupported reference type: {suffix}")
