from skiptlu.tasks.layout import default_word_layout
from skiptlu.tasks.understanding import TaskUnderstandingEngine


def test_default_word_layout_is_structured():
    layout = default_word_layout(include_toc=True, include_landscape=True)

    assert layout.include_toc is True
    assert layout.include_illustration_lists is True
    assert layout.landscape_before_level == 2
    assert layout.heading_styles[1].bold is True
    assert layout.heading_styles[3].italic is True


def test_understanding_attaches_content_and_layout():
    from pathlib import Path
    from skiptlu.models.activity import Activity, ModuleType
    from skiptlu.tasks.context import ActivityContext
    from skiptlu.references.models import DocumentRequirementHints, ParsedDocument

    context = ActivityContext(
        activity=Activity(id=51068, module=ModuleType.ASSIGNMENT, name="Word"),
        parsed_references=(
            ParsedDocument(
                path=Path("reference.pdf"),
                file_type="pdf",
                hints=DocumentRequirementHints(
                    headings=["CHƯƠNG 1. Demo"],
                    has_toc=True,
                    has_landscape_section=True,
                ),
            ),
        ),
    )

    spec = TaskUnderstandingEngine().understand(context)

    assert spec.content is not None
    assert spec.layout is not None
    assert spec.layout.include_toc is True
    assert spec.layout.landscape_before_level == 2
