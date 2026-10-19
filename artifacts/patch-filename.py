from pathlib import Path
p=Path(r"D:\LearningPesonal\Project\skiptlu\src\skiptlu\models\word_task.py")
s=p.read_text(encoding="utf-8")
s=s.replace("import re\n", "import re\nimport unicodedata\n")
old='''    @property
    def output_path(self) -> Path:
        stem = re.sub(r"[^\w\-.]+", "_", self.title, flags=re.UNICODE).strip("_")
        stem = stem[:120] or f"activity_{self.activity_id}"
        filename = f"{self.student.student_id}_{stem}.docx"
        return self.output_dir / filename
'''
new='''    @staticmethod
    def _ascii_name(value: str) -> str:
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
'''
assert old in s
p.write_text(s.replace(old,new),encoding="utf-8")
print("patched")
