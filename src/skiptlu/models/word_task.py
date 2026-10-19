from pathlib import Path
import re
import unicodedata

from pydantic import BaseModel

from skiptlu.tasks.content import ContentSpecification
from skiptlu.tasks.layout import LayoutSpecification
from skiptlu.tasks.specification import PracticalTaskSpecification


class StudentInfo(BaseModel):
    name: str
    student_id: str
    major: str
    year: int = 2026


class WordTaskSpecification(BaseModel):
    """Resolved specification consumed by the Word artifact provider."""

    activity_id: int
    title: str
    template_path: Path | None = None
    content_source_path: Path | None = None
    image_path: Path
    output_dir: Path
    student: StudentInfo
    task_specification: PracticalTaskSpecification | None = None
    content_specification: ContentSpecification
    layout_specification: LayoutSpecification

    def derived_headings(self, level: int) -> list[str]:
        return [
            item.title
            for item in self.content_specification.sections
            if item.level == level
        ]

    def derived_captions(self) -> list[str]:
        captions: list[str] = []
        captions.extend(item.caption for item in self.content_specification.figures)
        captions.extend(item.caption for item in self.content_specification.tables)
        return list(dict.fromkeys(captions))

    @staticmethod
    def _heading_level(text: str) -> int:
        if re.match(r"^CHƯƠNG\s+\d+\.", text, re.IGNORECASE):
            return 1
        if re.match(r"^\d+\.\d+\.\d+\.", text):
            return 3
        if re.match(r"^\d+\.\d+\.", text):
            return 2
        return 0

    @staticmethod
    def _ascii_name(value: str) -> str:
        value = value.replace("Đ", "D").replace("đ", "d")
        normalized = unicodedata.normalize("NFKD", value)
        return "".join(ch for ch in normalized if not unicodedata.combining(ch))

    @property
    def output_path(self) -> Path:
        metadata = self.task_specification.metadata if self.task_specification else {}

        explicit = metadata.get("output_filename")
        if isinstance(explicit, str) and explicit.strip():
            filename = explicit.strip()
            if not filename.lower().endswith(".docx"):
                filename += ".docx"
            return self.output_dir / filename

        content_stem = self.content_source_path.stem if self.content_source_path else ""
        content_stem = re.sub(
            r"^(?:File\s+)?B[ÀA]I\s+L[ÀA]M[_\s-]*",
            "",
            content_stem,
            flags=re.IGNORECASE,
        )
        content_stem = re.sub(
            r"^BaiLam[_\s-]*",
            "",
            content_stem,
            flags=re.IGNORECASE,
        )
        content_stem = re.sub(r"[^\w\-.]+", "_", content_stem, flags=re.UNICODE).strip("_")

        student_name = re.sub(
            r"[^A-Za-z0-9]+",
            "",
            self._ascii_name(self.student.name),
        )
        if content_stem:
            stem = f"{student_name}_{content_stem}" if student_name else content_stem
        else:
            title = self._ascii_name(self.title)
            title = re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_")
            stem = title or f"activity_{self.activity_id}"

        filename = f"{self.student.student_id}_{stem}.docx"
        return self.output_dir / filename
