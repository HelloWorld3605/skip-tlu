from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from skiptlu.tasks.context import ActivityContext

@dataclass(frozen=True)
class ReferenceRole:
    path: Path
    role: str
    reason: str


def classify_reference_roles(context: ActivityContext) -> tuple[ReferenceRole, ...]:
    explicit = context.metadata.get("reference_roles")
    explicit_map = explicit if isinstance(explicit, dict) else {}
    text = " ".join((context.description, *context.instructions, *(item.name for item in context.attachments))).casefold()
    format_words = ("file mẫu", "tệp mẫu", "theo mẫu", "giống mẫu", "định dạng theo", "trình bày theo", "template", "format")
    content_words = ("tài liệu tham khảo", "tham khảo nội dung", "nguồn tham khảo", "reference")
    wants_template = any(word in text for word in format_words)
    roles = []
    for item in context.attachments:
        if item.path is None:
            continue
        key_options = (item.name, str(item.path), item.path.name)
        explicit_role = next((str(explicit_map[key]) for key in key_options if key in explicit_map), None)
        if explicit_role:
            roles.append(ReferenceRole(item.path, explicit_role, "Explicit LLM/task reference role"))
            continue
        name = item.path.name.casefold()
        if item.path.suffix.casefold() in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
            roles.append(ReferenceRole(item.path, "asset", "Image attachment"))
        elif any(x in name for x in ("bailam", "bai_lam", "bài làm", "noi dung", "nội dung", "content", "answer", "submission")):
            roles.append(ReferenceRole(item.path, "content", "Filename identifies the editable content/source document"))
        elif wants_template and item.path.suffix.casefold() in {".pdf", ".docx"} and any(x in name for x in ("mau", "template", "thamkhao", "tham_khao", "reference")):
            roles.append(ReferenceRole(item.path, "template", "Formatting/sample language plus sample-like filename"))
        elif any(word in text for word in content_words):
            roles.append(ReferenceRole(item.path, "content", "Context identifies reference content"))
        else:
            roles.append(ReferenceRole(item.path, "reference", "No template role established"))
    return tuple(roles)
