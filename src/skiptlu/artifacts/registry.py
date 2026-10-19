from pathlib import Path

from skiptlu.artifacts.base import ArtifactProvider, WordArtifactProvider
from skiptlu.artifacts.enhancer_factory import build_word_enhancer_from_env
from skiptlu.artifacts.template import TemplateDecision, TemplateMode, materialize_template
from skiptlu.models.activity import Activity
from skiptlu.models.word_task import StudentInfo, WordTaskSpecification
from skiptlu.tasks.specification import ArtifactType, PracticalTaskSpecification


class ArtifactRegistry:
    """Resolve artifact generation strategy from the task specification."""

    def __init__(self, *, project_root: Path, student: StudentInfo, output_dir: Path | None = None) -> None:
        self.project_root = project_root
        self.student = student
        self.output_dir = output_dir or project_root / "artifacts" / "generated"

        def word_factory(activity: Activity, task: PracticalTaskSpecification | None = None) -> WordTaskSpecification:
            if task is None or task.content is None or task.layout is None:
                raise ValueError("Word artifact generation requires content and layout specifications")

            references = {path.name.lower(): path for path in task.source_files if path.is_file()}
            image = next(
                (p for p in references.values() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}),
                project_root / "artifacts" / "reference" / "Picture_De1.jpg",
            )

            strategy = str(task.metadata.get("artifact_strategy", TemplateMode.GENERATE.value))
            template: Path | None = None
            content_source: Path | None = None

            raw_content = task.metadata.get("content_files", [])
            content_candidates = [Path(x) for x in raw_content] if isinstance(raw_content, (list, tuple)) else []
            content_source = next((p for p in content_candidates if p.is_file() and p.suffix.lower() == ".docx"), None)

            if strategy == TemplateMode.USE_TEMPLATE.value:
                raw_templates = task.metadata.get("template_files", [])
                candidates = [Path(x) for x in raw_templates] if isinstance(raw_templates, (list, tuple)) else []
                source = next((p for p in candidates if p.is_file()), None)
                if source is None:
                    raise ValueError("use_template strategy requires an existing template_files entry")
                template = materialize_template(
                    TemplateDecision(
                        mode=TemplateMode.USE_TEMPLATE,
                        source=source,
                        reason="TaskUnderstandingEngine selected template mode",
                        confidence=1.0,
                    ),
                    cache_dir=project_root / "artifacts" / "template-cache",
                )
            else:
                # No PDF conversion in generate mode. A supplied DOCX may act as
                # the content source/starting document while remaining editable.
                template = next(
                    (p for p in references.values() if p.suffix.lower() == ".docx"),
                    None,
                )
                if content_source is None:
                    content_source = template

            return WordTaskSpecification(
                activity_id=activity.id,
                title=task.title,
                template_path=template,
                content_source_path=content_source,
                image_path=image,
                output_dir=self.output_dir,
                student=self.student,
                task_specification=task,
                content_specification=task.content,
                layout_specification=task.layout,
            )

        enhancer = build_word_enhancer_from_env(project_root)
        self._providers_by_activity: dict[int, ArtifactProvider] = {
            51068: WordArtifactProvider(word_factory, enhancer=enhancer),
        }
        self._providers_by_type: dict[ArtifactType, ArtifactProvider] = {
            ArtifactType.DOCX: WordArtifactProvider(word_factory, enhancer=enhancer),
        }

    def for_task(self, specification: PracticalTaskSpecification, activity: Activity) -> ArtifactProvider | None:
        return self._providers_by_type.get(specification.artifact_type) or self._providers_by_activity.get(activity.id)

    def for_activity(self, activity: Activity) -> ArtifactProvider | None:
        return self._providers_by_activity.get(activity.id)
