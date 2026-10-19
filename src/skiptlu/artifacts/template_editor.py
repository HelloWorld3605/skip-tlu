from __future__ import annotations

from docx import Document

from skiptlu.artifacts.content_controller import WordContentController
from skiptlu.artifacts.template_regions import TemplateFingerprint
from skiptlu.models.word_task import StudentInfo
from skiptlu.tasks.content_operations import ContentOperation, RegionContract


class TemplatePreservingEditor:
    """Edit a materialized template without rebuilding its layout."""

    def __init__(self, controller: WordContentController | None = None) -> None:
        self.controller = controller or WordContentController()

    @staticmethod
    def student_operations(student: StudentInfo) -> tuple[list[ContentOperation], list[RegionContract]]:
        values = (
            ("cover.student_name", "HỌ TÊN CỦA SINH VIÊN", student.name.upper()),
            ("cover.student_id", "MÃ CỦA SINH VIÊN", student.student_id.upper()),
            ("cover.major", "NGÀNH CỦA SINH VIÊN", student.major.upper()),
        )
        operations = [
            ContentOperation(
                operation="replace_text",
                target=target,
                value=value,
                region_id=region_id,
                required=True,
            )
            for region_id, target, value in values
        ]
        contracts = [
            RegionContract(
                region_id=region_id,
                allowed_operations={"replace_text"},
                required=True,
                target_pattern=target,
                max_occurrences=1,
            )
            for region_id, target, _ in values
        ]
        return operations, contracts

    def edit(
        self,
        doc: Document,
        *,
        student: StudentInfo,
        template_fingerprint: TemplateFingerprint,
        task_operations: list[ContentOperation] | None = None,
        task_contracts: list[RegionContract] | None = None,
    ) -> None:
        student_ops, student_contracts = self.student_operations(student)
        operations = [*student_ops, *(task_operations or [])]
        contracts_by_id = {item.region_id: item for item in student_contracts}
        contracts_by_id.update({item.region_id: item for item in (task_contracts or [])})

        self.controller.apply(
            doc,
            operations,
            list(contracts_by_id.values()),
            region_map=template_fingerprint.regions,
        )
