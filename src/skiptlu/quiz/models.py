from dataclasses import dataclass, field
from enum import Enum


class QuestionType(str, Enum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    TEXT = "text"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class QuizOption:
    value: str
    label: str


@dataclass(frozen=True)
class QuizQuestion:
    question_id: str
    number: int
    prompt: str
    question_type: QuestionType
    options: tuple[QuizOption, ...] = ()
    required: bool = True
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class QuizAnswer:
    question_id: str
    values: tuple[str, ...]
    source: str = "external"


@dataclass(frozen=True)
class QuizAnswerPlan:
    answers: tuple[QuizAnswer, ...] = ()

    def for_question(self, question_id: str) -> QuizAnswer | None:
        return next((item for item in self.answers if item.question_id == question_id), None)

    def is_complete_for(self, questions: tuple[QuizQuestion, ...]) -> bool:
        return all(
            (not question.required) or self.for_question(question.question_id) is not None
            for question in questions
        )
