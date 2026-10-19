from dataclasses import dataclass, field
from pathlib import Path
from skiptlu.models.activity import Activity
from skiptlu.references.models import ParsedDocument

@dataclass(frozen=True)
class ActivityAttachment:
    name: str
    path: Path | None = None
    url: str | None = None
    content_type: str | None = None

@dataclass(frozen=True)
class ActivityContext:
    activity: Activity
    description: str = ""
    instructions: tuple[str, ...] = ()
    attachments: tuple[ActivityAttachment, ...] = ()
    related_activity_names: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)
    parsed_references: tuple[ParsedDocument, ...] = ()

    def with_parsed_references(self, documents: tuple[ParsedDocument, ...]) -> "ActivityContext":
        return ActivityContext(
            activity=self.activity,
            description=self.description,
            instructions=self.instructions,
            attachments=self.attachments,
            related_activity_names=self.related_activity_names,
            metadata=dict(self.metadata),
            parsed_references=documents,
        )

    def with_attachment_paths(self, paths: dict[str, Path]) -> "ActivityContext":
        updated = tuple(
            ActivityAttachment(
                name=item.name,
                path=paths.get(item.url or "", item.path),
                url=item.url,
                content_type=item.content_type,
            )
            for item in self.attachments
        )
        return ActivityContext(
            activity=self.activity,
            description=self.description,
            instructions=self.instructions,
            attachments=updated,
            related_activity_names=self.related_activity_names,
            metadata=dict(self.metadata),
            parsed_references=self.parsed_references,
        )

    @classmethod
    def from_collected_data(cls, activity: Activity, data: dict[str, object]) -> "ActivityContext":
        raw_attachments = data.get("attachments", [])
        attachments = tuple(
            ActivityAttachment(
                name=str(item.get("name", "")),
                url=str(item.get("url")) if item.get("url") else None,
                content_type=str(item.get("content_type")) if item.get("content_type") else None,
            )
            for item in raw_attachments
            if isinstance(item, dict) and item.get("url")
        )
        raw_instructions = data.get("instructions", [])
        instructions = tuple(str(item) for item in raw_instructions if str(item).strip())
        raw_related = data.get("relatedActivities", [])
        related = tuple(str(item) for item in raw_related if str(item).strip())
        return cls(
            activity=activity,
            description=str(data.get("description", "")),
            instructions=instructions,
            attachments=attachments,
            related_activity_names=related,
            metadata={"completion": data.get("completion", [])},
        )
