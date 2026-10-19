from pathlib import Path

import pytest

from skiptlu.artifacts.template import (
    TemplateMode,
    TemplateDecision,
    materialize_template,
    resolve_template,
)
from skiptlu.models.activity import Activity, ModuleType
from skiptlu.tasks.context import ActivityAttachment, ActivityContext


def activity():
    return Activity(id=9001, module=ModuleType.ASSIGNMENT, name="Word task")


def test_pdf_reference_is_not_template_without_template_context(tmp_path):
    pdf = tmp_path / "reference.pdf"
    pdf.write_bytes(b"pdf")

    context = ActivityContext(
        activity=activity(),
        description="Đọc tài liệu tham khảo và tạo nội dung Word.",
        attachments=(ActivityAttachment("ThamKhao.pdf", pdf),),
    )

    decision = resolve_template(context)

    assert decision.mode is TemplateMode.GENERATE
    assert decision.source is None


def test_explicit_template_role_wins(tmp_path):
    pdf = tmp_path / "ThamKhao_Mau.pdf"
    pdf.write_bytes(b"pdf")

    context = ActivityContext(
        activity=activity(),
        description="Tạo tài liệu theo file mẫu.",
        attachments=(ActivityAttachment("ThamKhao_Mau.pdf", pdf),),
        metadata={"template_file": str(pdf), "artifact_strategy": "use_template"},
    )

    decision = resolve_template(context)

    assert decision.mode is TemplateMode.USE_TEMPLATE
    assert decision.source == pdf
    assert decision.confidence == 1.0


def test_template_pdf_is_converted_only_in_template_mode(tmp_path):
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"pdf")
    target = tmp_path / "sample.template.docx"

    class FakeConverter:
        def __init__(self):
            self.calls = []

        def convert(self, source: Path, output: Path) -> Path:
            self.calls.append((source, output))
            output.write_bytes(b"docx")
            return output

    converter = FakeConverter()
    decision = TemplateDecision(
        mode=TemplateMode.USE_TEMPLATE,
        source=pdf,
        reason="test",
        confidence=1.0,
    )

    result = materialize_template(
        decision,
        cache_dir=tmp_path / "cache",
        converter=converter,
    )

    assert result is not None
    assert result.exists()
    assert len(converter.calls) == 1


def test_docx_template_is_reused_without_conversion(tmp_path):
    docx = tmp_path / "sample.docx"
    docx.write_bytes(b"docx")

    class FakeConverter:
        def convert(self, source, output):
            raise AssertionError("DOCX template must not be converted")

    decision = TemplateDecision(
        mode=TemplateMode.USE_TEMPLATE,
        source=docx,
        reason="test",
        confidence=1.0,
    )

    assert materialize_template(
        decision,
        cache_dir=tmp_path / "cache",
        converter=FakeConverter(),
    ) == docx


def test_invalid_explicit_template_fails(tmp_path):
    missing = tmp_path / "missing.pdf"
    context = ActivityContext(
        activity=activity(),
        metadata={
            "artifact_strategy": "use_template",
            "template_file": str(missing),
        },
    )

    with pytest.raises(ValueError):
        resolve_template(context)
