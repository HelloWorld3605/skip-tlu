from skiptlu.client.session import MoodleSession
from skiptlu.handlers.base import ActivityHandler
from skiptlu.handlers.lesson import LessonHandler
from skiptlu.handlers.practical import AssignmentHandler
from skiptlu.handlers.simple import FeedbackHandler, H5PHandler, QuizHandler, ViewHandler
from pathlib import Path

from skiptlu.models.activity import Activity, ModuleType


class HandlerRouter:
    @staticmethod
    def _assignment_context_factory(session, artifact_registry):
        if session is None:
            return None

        async def collect(activity):
            context = await session.collect_activity_context(activity)
            downloader = getattr(session, "download_references", None)
            if downloader is not None:
                root = getattr(artifact_registry, "project_root", Path.cwd())
                context = await downloader(
                    context,
                    root / "artifacts" / "references" / str(activity.id),
                )
            parser = getattr(session, "parse_references", None)
            if parser is not None:
                context = await parser(context)
            return context

        return collect

    def __init__(self, session: MoodleSession | None = None, artifact_provider=None, artifact_registry=None):
        self.session = session
        self._handlers: dict[ModuleType, ActivityHandler] = {
            ModuleType.LESSON: LessonHandler(session=session),
            ModuleType.QUIZ: QuizHandler(session=session),
            ModuleType.ASSIGNMENT: AssignmentHandler(
                session=session,
                artifact_provider=artifact_provider,
                artifact_registry=artifact_registry,
                task_context_factory=self._assignment_context_factory(session, artifact_registry),
            ),
            ModuleType.FEEDBACK: FeedbackHandler(session=session),
            ModuleType.RESOURCE: ViewHandler(session=session),
            ModuleType.PAGE: ViewHandler(session=session),
            ModuleType.H5P: H5PHandler(session=session),
        }

    def for_activity(self, activity: Activity) -> ActivityHandler:
        try:
            return self._handlers[activity.module]
        except KeyError as exc:
            raise ValueError(f"Unsupported Moodle module: {activity.module}") from exc
