from pathlib import Path

p=Path(r"D:\LearningPesonal\Project\skiptlu\src\skiptlu\tasks\understanding.py")
s=p.read_text(encoding="utf-8")
s=s.replace(
    "from skiptlu.tasks.requirements import RequirementExtractor",
    "from skiptlu.tasks.requirements import RequirementExtractor\nfrom skiptlu.tasks.reference_roles import classify_reference_roles",
)
old='''        content = self._build_content_specification(context)
        return PracticalTaskSpecification(
'''
new='''        content = self._build_content_specification(context)
        roles = classify_reference_roles(context)
        template_roles = [item for item in roles if item.role == "template"]
        content_roles = [item for item in roles if item.role == "content"]
        explicit_strategy = context.metadata.get("artifact_strategy")
        strategy = str(explicit_strategy) if explicit_strategy else ("use_template" if template_roles else "generate")
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
        }
        return PracticalTaskSpecification(
'''
s=s.replace(old,new)
s=s.replace('''            metadata={
                "description": context.description,
                "instruction_count": len(context.instructions),
                "reference_facts": reference_facts,
                "content_specification": content.model_dump(),
            },
''','''            metadata=metadata,
''')
p.write_text(s,encoding="utf-8")

p=Path(r"D:\LearningPesonal\Project\skiptlu\src\skiptlu\artifacts\registry.py")
s=p.read_text(encoding="utf-8")
s=s.replace(
    "from skiptlu.models.word_task import StudentInfo, WordTaskSpecification",
    "from skiptlu.models.word_task import StudentInfo, WordTaskSpecification\nfrom skiptlu.artifacts.template import TemplateMode, TemplateDecision, materialize_template",
)
start=s.index("        def word_factory(")
end=s.index("\n        enhancer =", start)
factory='''        def word_factory(
            activity: Activity,
            task: PracticalTaskSpecification | None = None,
        ) -> WordTaskSpecification:
            if task is None:
                raise ValueError("Word artifact generation requires a task specification")
            if task.content is None or task.layout is None:
                raise ValueError("Word task specification must include content and layout")

            references = {
                path.name.lower(): path
                for path in task.source_files
                if path.is_file()
            }
            image = next(
                (p for p in references.values() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}),
                project_root / "artifacts" / "reference" / "Picture_De1.jpg",
            )

            raw_strategy = str(task.metadata.get("artifact_strategy", "generate"))
            strategy = TemplateMode.USE_TEMPLATE if raw_strategy == TemplateMode.USE_TEMPLATE.value else TemplateMode.GENERATE
            template_files = task.metadata.get("template_files", [])
            template_source = Path(template_files[0]) if template_files else None

            if strategy is TemplateMode.USE_TEMPLATE:
                if template_source is None or not template_source.is_file():
                    raise ValueError("Template strategy selected but template_files is empty or missing")
                decision = TemplateDecision(
                    TemplateMode.USE_TEMPLATE,
                    template_source,
                    "Resolved by TaskUnderstandingEngine",
                    1.0,
                )
                template = materialize_template(
                    decision,
                    cache_dir=project_root / "artifacts" / "template-cache",
                )
            else:
                template = next(
                    (p for p in references.values() if p.suffix.lower() == ".docx"),
                    None,
                )

            return WordTaskSpecification(
                activity_id=activity.id,
                title=task.title,
                template_path=template,
                image_path=image,
                output_dir=self.output_dir,
                student=self.student,
                task_specification=task,
                content_specification=task.content,
                layout_specification=task.layout,
            )
'''
s=s[:start]+factory+s[end:]
p.write_text(s,encoding="utf-8")

p=Path(r"D:\LearningPesonal\Project\skiptlu\src\skiptlu\models\word_task.py")
s=p.read_text(encoding="utf-8")
s=s.replace("    template_path: Path\r\n", "    template_path: Path | None\r\n")
s=s.replace("    template_path: Path
", "    template_path: Path | None
")
p.write_text(s,encoding="utf-8")
print("patched")
