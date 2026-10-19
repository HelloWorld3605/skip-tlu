from __future__ import annotations

from skiptlu.references.models import ParsedDocument
from skiptlu.tasks.specification import TaskRequirement


class RequirementExtractor:
    """Converts parsed reference facts into explicit, traceable requirements.

    Rules are intentionally conservative: a document structure is treated as
    evidence only when the reference itself contains that structure or the
    extracted text explicitly mentions the requirement.
    """

    def extract(self, documents: tuple[ParsedDocument, ...]) -> list[TaskRequirement]:
        requirements: list[TaskRequirement] = []
        seen: set[str] = set()

        def add(requirement: TaskRequirement) -> None:
            if requirement.key not in seen:
                seen.add(requirement.key)
                requirements.append(requirement)

        for document in documents:
            source = str(document.path)
            text = "\\n".join(p.text for p in document.paragraphs)
            lowered = text.lower()
            hints = document.hints

            if hints.headings:
                add(TaskRequirement(
                    key="document_heading_structure",
                    description="Preserve the heading hierarchy found in the reference document.",
                    metadata={
                        "headings": hints.headings,
                        "source": source,
                        "evidence": "reference_heading_styles",
                    },
                ))

            has_table_evidence = bool(document.tables) or any(
                caption.lower().startswith("bảng ") for caption in hints.captions
            )
            if has_table_evidence:
                add(TaskRequirement(
                    key="document_table",
                    description="Include the table structure represented by the reference.",
                    metadata={
                        "table_count": len(document.tables),
                        "source": source,
                        "evidence": "reference_tables",
                    },
                ))

            has_image_evidence = bool(document.images) or any(
                caption.lower().startswith(("ảnh ", "hình ", "figure "))
                for caption in hints.captions
            )
            if has_image_evidence:
                add(TaskRequirement(
                    key="document_images",
                    description="Include the required image content represented by the reference.",
                    metadata={
                        "image_count": len(document.images),
                        "source": source,
                        "evidence": "reference_images",
                    },
                ))

            if hints.captions:
                add(TaskRequirement(
                    key="captions",
                    description="Use captions for the illustrated/table content shown in the reference.",
                    metadata={
                        "captions": hints.captions,
                        "source": source,
                        "evidence": "reference_caption_paragraphs",
                    },
                ))

            if hints.has_toc or "mục lục" in lowered or "table of contents" in lowered:
                add(TaskRequirement(
                    key="table_of_contents",
                    description="Include a table of contents.",
                    value=True,
                    metadata={"source": source, "evidence": "toc_field_or_explicit_text"},
                ))

            if hints.has_footnotes or "footnote" in lowered or "chú thích cuối trang" in lowered:
                add(TaskRequirement(
                    key="footnotes",
                    description="Include footnotes where required by the reference.",
                    value=True,
                    metadata={"source": source, "evidence": "footnote_part_or_explicit_text"},
                ))

            if hints.has_landscape_section or any(
                marker in lowered
                for marker in ("landscape", "khổ ngang", "hướng ngang", "trang ngang")
            ):
                add(TaskRequirement(
                    key="landscape_section",
                    description="Include a landscape-oriented section where indicated by the reference.",
                    value=True,
                    metadata={"source": source, "evidence": "landscape_section_or_explicit_text"},
                ))

            if "times new roman" in lowered:
                add(TaskRequirement(
                    key="font_times_new_roman",
                    description="Use Times New Roman where specified by the reference.",
                    value="Times New Roman",
                    metadata={"source": source, "evidence": "explicit_text"},
                ))

        return requirements
