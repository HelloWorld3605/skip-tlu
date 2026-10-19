from pathlib import Path

from skiptlu.references.models import DocumentParagraph, DocumentRequirementHints, ParsedDocument


class PdfReferenceParser:
    """Extracts text from Moodle PDF references when pypdf is available."""

    def parse(self, path: Path) -> ParsedDocument:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError(
                "PDF parsing requires pypdf. Install with: pip install 'skiptlu[pdf]'"
            ) from exc

        reader = PdfReader(str(path))
        paragraphs: list[DocumentParagraph] = []
        headings: list[str] = []
        captions: list[str] = []
        has_toc = False
        has_footnotes = False

        for page_number, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if not text:
                continue
            for raw_line in text.splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                normalized = self._normalize_heading_or_caption(line)
                level = self._heading_level(normalized)
                if level is not None:
                    headings.append(normalized)
                if self._is_caption(normalized):
                    captions.append(normalized)
                lowered = line.lower()
                if "mục lục" in lowered or "table of contents" in lowered:
                    has_toc = True
                if "footnote" in lowered or "chú thích cuối trang" in lowered:
                    has_footnotes = True
                paragraphs.append(
                    DocumentParagraph(text=line, style=None, level=level, page=page_number)
                )

        headings = list(dict.fromkeys(headings))
        captions = list(dict.fromkeys(captions))

        return ParsedDocument(
            path=path,
            file_type="pdf",
            paragraphs=paragraphs,
            hints=DocumentRequirementHints(
                headings=headings,
                captions=captions,
                has_toc=has_toc,
                has_footnotes=has_footnotes,
                has_landscape_section=False,
            ),
            metadata={"page_count": len(reader.pages)},
        )

    @staticmethod
    def _normalize_heading_or_caption(line: str) -> str:
        import re
        return re.sub(r"\s*\.{3,}\s*\d+\s*$", "", line).strip()

    @staticmethod
    def _heading_level(line: str) -> int | None:
        import re
        if re.match(r"^CHƯƠNG\s+\d+\.", line, re.IGNORECASE):
            return 1
        if re.match(r"^\d+\.\d+\.\s+", line):
            return 2
        if re.match(r"^\d+\.\d+\.\d+\.\s+", line):
            return 3
        return None

    @staticmethod
    def _is_caption(line: str) -> bool:
        lowered = line.lower()
        return lowered.startswith(("ảnh ", "bảng ", "hình ", "table ", "figure "))
