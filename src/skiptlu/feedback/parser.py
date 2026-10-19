from __future__ import annotations

from bs4 import BeautifulSoup

from .models import FeedbackOption, FeedbackQuestion, FeedbackQuestionType


class MoodleFeedbackParser:
    """Parse Moodle mod_feedback forms without generating responses."""

    def parse(self, html: str) -> tuple[FeedbackQuestion, ...]:
        soup = BeautifulSoup(html, "html.parser")
        questions = []

        for index, node in enumerate(
            soup.select(".feedback_itemlist .feedback_item, .feedback_item"),
            start=1,
        ):
            control = node.select_one(
                "input, textarea, select"
            )
            if control is None:
                continue

            question_id = (
                control.get("name")
                or control.get("id")
                or f"feedback-{index}"
            )
            prompt_node = node.select_one(
                ".feedback_item_label, .feedback_item_label_text, label, .qtext"
            )
            prompt = self._text(prompt_node) or self._text(node)
            qtype = self._question_type(control)
            options = tuple(self._options(node, qtype))
            required = bool(
                node.select_one(".required, [aria-required='true'], input[required], textarea[required], select[required]")
            )

            questions.append(
                FeedbackQuestion(
                    question_id=question_id,
                    number=index,
                    prompt=prompt,
                    question_type=qtype,
                    options=options,
                    required=required,
                )
            )

        return tuple(questions)

    @staticmethod
    def _text(node) -> str:
        return " ".join(node.get_text(" ", strip=True).split()) if node else ""

    @staticmethod
    def _question_type(control) -> FeedbackQuestionType:
        tag = control.name
        if tag == "textarea":
            return FeedbackQuestionType.TEXTAREA
        if tag == "select":
            return FeedbackQuestionType.SELECT
        if tag == "input":
            kind = (control.get("type") or "text").lower()
            return {
                "radio": FeedbackQuestionType.RADIO,
                "checkbox": FeedbackQuestionType.CHECKBOX,
                "text": FeedbackQuestionType.TEXT,
            }.get(kind, FeedbackQuestionType.UNKNOWN)
        return FeedbackQuestionType.UNKNOWN

    def _options(self, node, qtype):
        if qtype == FeedbackQuestionType.SELECT:
            for option in node.select("option"):
                if option.get("value") is not None:
                    yield FeedbackOption(
                        value=option.get("value", ""),
                        label=self._text(option),
                    )
            return

        if qtype not in {
            FeedbackQuestionType.RADIO,
            FeedbackQuestionType.CHECKBOX,
        }:
            return

        for control in node.select("input[type=radio], input[type=checkbox]"):
            value = control.get("value", "")
            control_id = control.get("id", "")
            label = node.select_one(f"label[for='{control_id}']") if control_id else None
            if label is None:
                parent = control.find_parent("label")
                label_text = self._text(parent)
            else:
                label_text = self._text(label)
            yield FeedbackOption(value=value, label=label_text)
