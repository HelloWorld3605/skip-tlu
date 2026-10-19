from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import shutil

from skiptlu.tasks.context import ActivityContext


class TemplateMode(str, Enum):
    AUTO = "auto"
    USE_TEMPLATE = "use_template"
    GENERATE = "generate"


@dataclass(frozen=True)
class TemplateDecision:
    mode: TemplateMode
    source: Path | None
    reason: str
    confidence: float


_TEMPLATE_TERMS = (
    "file mẫu", "tệp mẫu", "mau", "template", "format", "định dạng theo",
    "trình bày theo", "theo mẫu", "giống mẫu", "dựa theo mẫu",
)

_CONTENT_ONLY_TERMS = (
    "tài liệu tham khảo", "tham khảo nội dung", "reference", "nguồn tham khảo",
)


def _text(context: ActivityContext) -> str:
    attachment_names = " ".join(item.name for item in context.attachments)
    return " ".join(
        (context.description, *context.instructions, attachment_names)
    ).casefold()


def _path_from_metadata(context: ActivityContext) -> Path | None:
    raw = context.metadata.get("template_file")
    if isinstance(raw, (str, Path)):
        path = Path(raw)
        return path if path.is_file() else None

    raw_files = context.metadata.get("template_files")
    if isinstance(raw_files, (list, tuple)):
        for value in raw_files:
            path = Path(value)
            if path.is_file():
                return path
    return None


def resolve_template(context: ActivityContext) -> TemplateDecision:
    """Resolve whether a task should use a layout template.

    Explicit LLM/task metadata wins. AUTO only selects a template when the
    task context actually describes a template/format requirement. A generic
    PDF reference is never treated as a template merely because it is a PDF.
    """
    explicit = context.metadata.get("artifact_strategy")
    source = _path_from_metadata(context)

    if isinstance(explicit, str):
        try:
            mode = TemplateMode(explicit)
        except ValueError:
            mode = TemplateMode.AUTO
        if mode is TemplateMode.GENERATE:
            return TemplateDecision(mode, None, "Explicit task strategy: generate", 1.0)
        if mode is TemplateMode.USE_TEMPLATE:
            if source is None:
                raise ValueError("Task requested template mode but no template_file/template_files was supplied")
            return TemplateDecision(mode, source, "Explicit task strategy: use template", 1.0)

    text = _text(context)
    has_template_language = any(term in text for term in _TEMPLATE_TERMS)
    has_content_only_language = any(term in text for term in _CONTENT_ONLY_TERMS)

    if source is not None and has_template_language:
        return TemplateDecision(
            TemplateMode.USE_TEMPLATE,
            source,
            "Context explicitly describes a template/format source",
            0.95,
        )

    if source is not None and not has_content_only_language:
        # A role explicitly assigned by the collector/LLM is enough even if
        # natural-language instructions are terse.
        return TemplateDecision(
            TemplateMode.USE_TEMPLATE,
            source,
            "A template source was explicitly assigned in task metadata",
            0.90,
        )

    return TemplateDecision(
        TemplateMode.GENERATE,
        None,
        "No explicit template context; references remain content/reference sources",
        0.85,
    )


class WordPdfTemplateConverter:
    """Convert a PDF template through the installed desktop Word app.

    Microsoft documents that opening a PDF in desktop Word creates an editable
    Word copy while attempting to preserve layout. The original PDF remains
    untouched. This converter is deliberately isolated so non-template tasks
    never invoke PDF conversion.
    """

    def convert(self, source: Path, output: Path) -> Path:
        if source.suffix.casefold() != ".pdf":
            return source
        if not source.is_file():
            raise FileNotFoundError(source)

        output.parent.mkdir(parents=True, exist_ok=True)
        import win32com.client as win32

        word = win32.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        document = None
        try:
            document = word.Documents.Open(str(source.resolve()), ReadOnly=True, ConfirmConversions=False)
            # 16 = wdFormatDocumentDefault (DOCX).
            document.SaveAs2(str(output.resolve()), FileFormat=16, AddToRecentFiles=False)
            return output
        finally:
            try:
                if document is not None:
                    document.Close(SaveChanges=False)
            finally:
                word.Quit()


def materialize_template(
    decision: TemplateDecision,
    *,
    cache_dir: Path,
    converter: WordPdfTemplateConverter | None = None,
) -> Path | None:
    if decision.mode is not TemplateMode.USE_TEMPLATE or decision.source is None:
        return None

    source = decision.source
    cache_dir.mkdir(parents=True, exist_ok=True)

    if source.suffix.casefold() == ".docx":
        return source

    if source.suffix.casefold() != ".pdf":
        raise ValueError(f"Unsupported template format: {source.suffix}")

    target = cache_dir / f"{source.stem}.template.docx"
    if target.exists() and target.stat().st_mtime >= source.stat().st_mtime:
        return target

    converter = converter or WordPdfTemplateConverter()
    return converter.convert(source, target)
