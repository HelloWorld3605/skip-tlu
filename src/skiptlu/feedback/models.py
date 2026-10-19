from dataclasses import dataclass, field
from enum import Enum


class FeedbackQuestionType(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    SELECT = "select"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class FeedbackOption:
    value: str
    label: str


@dataclass(frozen=True)
class FeedbackQuestion:
    question_id: str
    number: int
    prompt: str
    question_type: FeedbackQuestionType
    options: tuple[FeedbackOption, ...] = ()
    required: bool = False
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class FeedbackResponse:
    question_id: str
    values: tuple[str, ...]
    source: str = "external"


@dataclass(frozen=True)
class FeedbackResponsePlan:
    responses: tuple[FeedbackResponse, ...] = ()

    def for_question(self, question_id: str) -> FeedbackResponse | None:
        return next(
            (item for item in self.responses if item.question_id == question_id),
            None,
        )

    def is_complete_for(
        self,
        questions: tuple[FeedbackQuestion, ...],
    ) -> bool:
        return all(
            (not question.required)
            or self.for_question(question.question_id) is not None
            for question in questions
        )
