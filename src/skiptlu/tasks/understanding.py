from skiptlu.tasks.context import ActivityContext
from skiptlu.tasks.content import ContentFigure, ContentSection, ContentSpecification, ContentTable
from skiptlu.tasks.layout import default_word_layout
from skiptlu.tasks.reference_roles import classify_reference_roles
from skiptlu.tasks.content_operations import ContentOperation
from skiptlu.tasks.specification import ArtifactType, PracticalTaskSpecification, TaskRequirement
from skiptlu.tasks.requirements import RequirementExtractor


class TaskUnderstandingEngine:
    """Turn Moodle/reference facts into a deterministic, context-aware task plan."""

    def __init__(self, requirement_extractor: RequirementExtractor | None = None) -> None:
        self.requirement_extractor = requirement_extractor or RequirementExtractor()

    def understand(self, context: ActivityContext) -> PracticalTaskSpecification:
        if context.activity.module.value != "assign":
            raise ValueError(f"Activity {context.activity.id} is not a practical assignment")

        requirements = [
            TaskRequirement(key=f"instruction_{i}", description=value)
            for i, value in enumerate(context.instructions, 1)
        ]
        requirements.extend(self.requirement_extractor.extract(context.parsed_references))

        reference_facts = []
        for document in context.parsed_references:
            reference_facts.append({
                "source": str(document.path),
                "type": document.file_type,
                "paragraph_count": len(document.paragraphs),
                "table_count": len(document.tables),
                "image_count": len(document.images),
                "headings": list(document.hints.headings),
                "tables": [table.rows for table in document.tables],
                "paragraphs": [item.text for item in document.paragraphs],
                "hints": document.hints.model_dump(),
                "sections": [item.model_dump() for item in document.sections],
            })

        roles = classify_reference_roles(context)
        template_roles = [item for item in roles if item.role == "template"]
        content_roles = [item for item in roles if item.role == "content"]
        explicit_strategy = context.metadata.get("artifact_strategy")
        strategy = str(explicit_strategy) if explicit_strategy else (
            "use_template" if template_roles else "generate"
        )

        content = self._build_content_specification(context)
        raw_operations = context.metadata.get("content_operations", [])
        content_operations = [ContentOperation.model_validate(item) for item in raw_operations if isinstance(item, dict)]
        metadata = {
            "description": context.description,
            "instruction_count": len(context.instructions),
            "reference_facts": reference_facts,
            "content_specification": content.model_dump(),
            "reference_roles": [
                {"path": str(item.path), "role": item.role, "reason": item.reason}
                for item in roles
            ],
            "artifact_strategy": strategy,
            "template_files": [str(item.path) for item in template_roles],
            "content_files": [str(item.path) for item in content_roles],
            # LLM can override these with an explicit content plan without
            # changing the renderer's layout strategy.
            "content_operations": [item.model_dump() for item in content_operations],
        }

        return PracticalTaskSpecification(
            activity_id=context.activity.id,
            title=context.activity.name,
            artifact_type=self._artifact_type(context),
            requirements=requirements,
            source_files=[item.path for item in context.attachments if item.path is not None],
            content=content,
            layout=default_word_layout(
                include_toc=content.include_toc,
                include_landscape=content.include_landscape_section,
            ),
            content_operations=content_operations,
            metadata=metadata,
        )

    @staticmethod
    def _build_content_specification(context: ActivityContext) -> ContentSpecification:
        sections: list[ContentSection] = []
        figures: list[ContentFigure] = []
        tables: list[ContentTable] = []
        include_toc = False
        include_footnotes = False
        include_landscape = False

        for document in context.parsed_references:
            for heading in document.hints.headings:
                level = 1
                import re
                if re.match(r"^\d+\.\d+\.\d+\.", heading):
                    level = 3
                elif re.match(r"^\d+\.\d+\.", heading):
                    level = 2
                sections.append(ContentSection(level=level, title=heading, source=str(document.path)))

            for caption in document.hints.captions:
                lowered = caption.lower().strip()
                if lowered.startswith("bảng biểu:"):
                    continue
                if lowered.startswith("bảng "):
                    tables.append(ContentTable(label="Bảng", caption=caption, source=str(document.path)))
                elif lowered.startswith("ảnh "):
                    figures.append(ContentFigure(label="Ảnh", caption=caption, source=str(document.path)))

            include_toc = include_toc or document.hints.has_toc
            include_footnotes = include_footnotes or document.hints.has_footnotes
            include_landscape = include_landscape or document.hints.has_landscape_section

        unique_sections: list[ContentSection] = []
        seen_sections: set[tuple[int, str]] = set()
        for item in sections:
            key = (item.level, " ".join(item.title.split()).strip().lower())
            if key not in seen_sections:
                seen_sections.add(key)
                unique_sections.append(item)

        unique_figures: list[ContentFigure] = []
        seen_figures: set[str] = set()
        for item in figures:
            key = " ".join(item.caption.split()).strip().lower()
            if key not in seen_figures:
                seen_figures.add(key)
                unique_figures.append(item)

        unique_tables: list[ContentTable] = []
        seen_tables: set[str] = set()
        for item in tables:
            key = " ".join(item.caption.split()).strip().lower()
            if key not in seen_tables:
                seen_tables.add(key)
                unique_tables.append(item)

        include_landscape = include_landscape or bool(unique_tables)

        return ContentSpecification(
            title=context.activity.name,
            source_documents=list(dict.fromkeys(str(document.path) for document in context.parsed_references)),
            sections=unique_sections,
            figures=unique_figures,
            tables=unique_tables,
            include_toc=include_toc,
            include_footnotes=include_footnotes,
            include_landscape_section=include_landscape,
        )

    @staticmethod
    def _artifact_type(context: ActivityContext) -> ArtifactType:
        declared = context.metadata.get("artifact_type")
        if isinstance(declared, str):
            try:
                return ArtifactType(declared.lower())
            except ValueError:
                pass

        names = " ".join(
            f"{item.name} {item.url or ''}".lower()
            for item in context.attachments
        )
        description = context.description.lower()
        if ".pptx" in names or "powerpoint" in description:
            return ArtifactType.PPTX
        if ".xlsx" in names or "excel" in description:
            return ArtifactType.XLSX
        if ".docx" in names or "word" in description:
            return ArtifactType.DOCX
        return ArtifactType.EXISTING
