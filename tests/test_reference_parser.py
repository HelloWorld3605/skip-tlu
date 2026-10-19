from pathlib import Path

from docx import Document

from skiptlu.references.docx import DocxReferenceParser
from skiptlu.references.models import DocumentParagraph


def test_docx_parser_extracts_headings_tables_and_images(tmp_path):
    path = tmp_path / "reference.docx"
    doc = Document()
    doc.add_heading("CHƯƠNG 1. GIỚI THIỆU", level=1)
    doc.add_paragraph("Nội dung mẫu")
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Tên"
    table.cell(0, 1).text = "Giá trị"
    table.cell(1, 0).text = "A"
    table.cell(1, 1).text = "B"
    doc.save(path)

    parsed = DocxReferenceParser().parse(path)

    assert parsed.file_type == "docx"
    assert any(p.level == 1 for p in parsed.paragraphs)
    assert parsed.tables[0].rows == [["Tên", "Giá trị"], ["A", "B"]]
    assert parsed.metadata["section_count"] == 1


def test_reference_context_keeps_parsed_documents(tmp_path):
    from skiptlu.models.activity import Activity, ModuleType
    from skiptlu.tasks.context import ActivityContext
    from skiptlu.references.models import ParsedDocument

    activity = Activity(id=1, module=ModuleType.ASSIGNMENT, name="A")
    document = ParsedDocument(
        path=tmp_path / "a.docx",
        file_type="docx",
        paragraphs=[DocumentParagraph(text="Heading", level=1)],
    )
    context = ActivityContext(activity=activity).with_parsed_references((document,))

    assert context.parsed_references[0].paragraphs[0].level == 1
