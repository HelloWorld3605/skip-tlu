from __future__ import annotations

from bs4 import BeautifulSoup

from .models import QuestionType, QuizOption, QuizQuestion


class MoodleQuizParser:
    """Parse quiz questions from a Moodle attempt page without solving them."""

    def parse(self, html: str) -> tuple[QuizQuestion, ...]:
        soup = BeautifulSoup(html, "html.parser")
        questions = []

        nodes = soup.select(".que")
        for index, node in enumerate(nodes, start=1):
            question_id = self._question_id(node, index)
            prompt = self._text(node.select_one(".qtext"))
            qtype = self._question_type(node)
            options = tuple(self._options(node, qtype))
            questions.append(
                QuizQuestion(
                    question_id=question_id,
                    number=index,
                    prompt=prompt,
                    question_type=qtype,
                    options=options,
                    required=True,
                )
            )

        return tuple(questions)

    @staticmethod
    def _question_id(node, fallback: int) -> str:
        value = node.get("id", "")
        if value.startswith("question-"):
            return value.removeprefix("question-")
        return str(fallback)

    @staticmethod
    def _text(node) -> str:
        return " ".join(node.get_text(" ", strip=True).split()) if node else ""

    def _question_type(self, node) -> QuestionType:
        if node.select_one("input[type=radio]"):
            labels = [self._text(label) for label in node.select("label")]
            if any(label.lower() in {"true", "false", "đúng", "sai"} for label in labels):
                return QuestionType.TRUE_FALSE
            return QuestionType.SINGLE_CHOICE

        if node.select_one("input[type=checkbox]"):
            return QuestionType.MULTIPLE_CHOICE

        if node.select_one("textarea, input[type=text]"):
            return QuestionType.TEXT

        return QuestionType.UNKNOWN

    def _options(self, node, qtype: QuestionType):
        if qtype not in {
            QuestionType.SINGLE_CHOICE,
            QuestionType.MULTIPLE_CHOICE,
            QuestionType.TRUE_FALSE,
        }:
            return []

        for control in node.select("input[type=radio], input[type=checkbox]"):
            value = control.get("value", "")
            control_id = control.get("id", "")
            label = node.select_one(f"label[for='{control_id}']") if control_id else None
            if label is None:
                parent = control.find_parent(["label", "div"])
                label_text = self._text(parent)
            else:
                label_text = self._text(label)
            yield QuizOption(value=value, label=label_text)
