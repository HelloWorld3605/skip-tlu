from pathlib import Path

from skiptlu.references.models import (
    DocumentImage,
    DocumentParagraph,
    DocumentRequirementHints,
    DocumentSection,
    DocumentTable,
    ParsedDocument,
)
from skiptlu.tasks.requirements import RequirementExtractor


def test_requirement_extractor_uses_reference_evidence():
    document = ParsedDocument(
        path=Path("reference.docx"),
        file_type="docx",
        paragraphs=[
            DocumentParagraph(text="GIỚI THIỆU", style="Heading 1", level=1),
            DocumentParagraph(text="Ảnh 1.1. Chiang Mai", style="Caption"),
        ],
        tables=[DocumentTable(rows=[["A", "B"]])],
        images=[DocumentImage(name="image1.jpg")],
        sections=[DocumentSection(orientation="landscape")],
        hints=DocumentRequirementHints(
            headings=["GIỚI THIỆU"],
            captions=["Ảnh 1.1. Chiang Mai"],
            has_toc=True,
            has_footnotes=True,
            has_landscape_section=True,
        ),
    )

    requirements = RequirementExtractor().extract((document,))
    keys = {item.key for item in requirements}

    assert {
        "document_heading_structure",
        "document_table",
        "document_images",
        "captions",
        "table_of_contents",
        "footnotes",
        "landscape_section",
    } <= keys


def test_requirement_extractor_deduplicates_across_documents(tmp_path):
    first = ParsedDocument(
        path=tmp_path / "a.docx",
        file_type="docx",
        hints=DocumentRequirementHints(headings=["A"]),
    )
    second = ParsedDocument(
        path=tmp_path / "b.docx",
        file_type="docx",
        hints=DocumentRequirementHints(headings=["B"]),
    )

    requirements = RequirementExtractor().extract((first, second))

    assert [item.key for item in requirements].count("document_heading_structure") == 1
