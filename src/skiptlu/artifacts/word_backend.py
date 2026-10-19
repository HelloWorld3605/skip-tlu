from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from docx import Document


@runtime_checkable
class WordBackend(Protocol):
    name: str

    def open(self, template_path: Path | None) -> Document:
        ...

    def save(self, document: Document, output_path: Path) -> None:
        ...


class NativeWordBackend:
    name = "native"

    def open(self, template_path: Path | None) -> Document:
        return Document(str(template_path)) if template_path else Document()

    def save(self, document: Document, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        document.save(str(output_path))
