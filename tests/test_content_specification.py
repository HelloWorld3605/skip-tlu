from pathlib import Path

from skiptlu.models.activity import Activity, ModuleType
from skiptlu.references.models import DocumentRequirementHints, ParsedDocument
from skiptlu.tasks.context import ActivityContext
from skiptlu.tasks.understanding import TaskUnderstandingEngine


def test_understanding_builds_content_specification():
    activity = Activity(id=51068, module=ModuleType.ASSIGNMENT, name="Word")
    context = ActivityContext(
        activity=activity,
        parsed_references=(
            ParsedDocument(
                path=Path("reference.pdf"),
                file_type="pdf",
                hints=DocumentRequirementHints(
                    headings=[
                        "CHƯƠNG 1. GIỚI THIỆU",
                        "1.1. Phần A",
                        "1.1.1. Chi tiết",
                    ],
                    captions=["Ảnh 1.1. Minh họa", "Bảng 2.1. Dữ liệu"],
                    has_toc=True,
                    has_footnotes=True,
                ),
            ),
        ),
    )

    spec = TaskUnderstandingEngine().understand(context)
    content = spec.metadata["content_specification"]

    assert [item["level"] for item in content["sections"]] == [1, 2, 3]
    assert len(content["figures"]) == 1
    assert len(content["tables"]) == 1
    assert content["include_toc"] is True
    assert content["include_footnotes"] is True
