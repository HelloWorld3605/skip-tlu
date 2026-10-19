from __future__ import annotations

import re

from docx import Document

from skiptlu.artifacts.template_regions import TemplateRegion, fingerprint_document
from skiptlu.tasks.content_operations import ContentOperation, RegionContract


class ContentControlError(ValueError):
    pass


class WordContentController:
    """Apply only explicit, deterministic content operations.

    Region contracts form an allow-list between the LLM/task contract and the
    Word mutator. Layout-changing operations are rejected unless the template
    explicitly permits them for the addressed region.
    """

    _SUPPORTED = {
        "replace_text",
        "replace_paragraph",
        "insert_after",
        "delete_paragraph",
    }

    def apply(
        self,
        doc: Document,
        operations: list[ContentOperation],
        region_contracts: list[RegionContract] | None = None,
        region_map: tuple[TemplateRegion, ...] | None = None,
    ) -> None:
        contracts = {contract.region_id: contract for contract in (region_contracts or [])}

        for operation in operations:
            self._validate_operation(operation, contracts)

            matches = self._resolve_matches(doc, operation, region_map)

            if operation.occurrence is not None:
                index = operation.occurrence
                matches = matches[index:index + 1] if 0 <= index < len(matches) else []

            if not matches:
                if operation.required:
                    locator = operation.region_id or operation.target
                    raise ContentControlError(
                        f"Required content target not found: {locator!r}"
                    )
                continue

            contract = contracts.get(operation.region_id) if operation.region_id else None
            if contract and len(matches) > contract.max_occurrences:
                raise ContentControlError(
                    f"Region {contract.region_id!r} matched {len(matches)} paragraphs; "
                    f"contract allows at most {contract.max_occurrences}"
                )

            paragraph = matches[0]
            value = operation.value or ""

            if operation.operation == "replace_text":
                if not operation.target:
                    raise ContentControlError(
                        "replace_text requires a target when using region_id"
                    )
                self._replace_text(paragraph, operation.target, value)
            elif operation.operation == "replace_paragraph":
                paragraph.text = value
            elif operation.operation == "insert_after":
                new = doc.add_paragraph(value)
                new.style = paragraph.style
                paragraph._p.addnext(new._p)
            elif operation.operation == "delete_paragraph":
                paragraph._element.getparent().remove(paragraph._element)

    def _validate_operation(
        self,
        operation: ContentOperation,
        contracts: dict[str, RegionContract],
    ) -> None:
        if operation.operation not in self._SUPPORTED:
            raise ContentControlError(
                f"Unsupported content operation: {operation.operation!r}"
            )

        if not operation.target and not operation.region_id:
            raise ContentControlError(
                "Content operation requires target or region_id"
            )

        if operation.occurrence is not None and operation.occurrence < 0:
            raise ContentControlError("occurrence must be >= 0")

        if operation.region_id:
            contract = contracts.get(operation.region_id)
            if contract is None:
                raise ContentControlError(
                    f"No region contract declared for: {operation.region_id!r}"
                )
            if operation.operation not in contract.allowed_operations:
                raise ContentControlError(
                    f"Operation {operation.operation!r} is not allowed in "
                    f"region {operation.region_id!r}"
                )
            if operation.required and not contract.required:
                # A caller cannot make an optional contract required by accident.
                raise ContentControlError(
                    f"Operation for optional region {operation.region_id!r} "
                    "cannot be marked required"
                )
            if contract.target_pattern and operation.target:
                if re.fullmatch(contract.target_pattern, operation.target) is None:
                    raise ContentControlError(
                        f"Target does not match contract for region "
                        f"{operation.region_id!r}: {operation.target!r}"
                    )
        elif contracts:
            # Once a template declares region contracts, an unscoped mutation is
            # intentionally forbidden: this is the main safety boundary.
            raise ContentControlError(
                "Unscoped content operation is forbidden when region contracts exist"
            )

    @staticmethod
    def _resolve_matches(
        doc: Document,
        operation: ContentOperation,
        region_map: tuple[TemplateRegion, ...] | None = None,
    ):
        if operation.region_id:
            regions = region_map if region_map is not None else fingerprint_document(doc).regions
            region = next(
                (item for item in regions if item.id == operation.region_id),
                None,
            )
            if region is None:
                return []
            return [
                doc.paragraphs[index]
                for index in region.paragraph_indices
                if index < len(doc.paragraphs)
            ]

        return [p for p in doc.paragraphs if operation.target in p.text]

    @staticmethod
    def _replace_text(paragraph, target: str, value: str) -> None:
        # Keep run-level formatting whenever the target is contained in one run.
        for run in paragraph.runs:
            if target in run.text:
                run.text = run.text.replace(target, value, 1)
                return

        # PDF->DOCX conversion can split one visible string across runs.
        # Controlled fallback: rebuild only this paragraph.
        full = paragraph.text
        if target not in full:
            raise ContentControlError(f"Content target disappeared: {target!r}")

        replacement = full.replace(target, value, 1)
        style = paragraph.style
        paragraph.text = replacement
        paragraph.style = style
