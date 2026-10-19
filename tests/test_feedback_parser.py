from skiptlu.feedback.models import FeedbackQuestionType
from skiptlu.feedback.parser import MoodleFeedbackParser


def test_parse_feedback_controls():
    html = """
    <div class="feedback_itemlist">
      <div class="feedback_item">
        <div class="feedback_item_label">How useful was this?</div>
        <input type="radio" name="resp_1" value="1" id="r1">
        <label for="r1">Very useful</label>
        <input type="radio" name="resp_1" value="2" id="r2">
        <label for="r2">Not useful</label>
      </div>
      <div class="feedback_item">
        <div class="feedback_item_label">Additional comments</div>
        <textarea name="resp_2"></textarea>
      </div>
    </div>
    """
    questions = MoodleFeedbackParser().parse(html)

    assert len(questions) == 2
    assert questions[0].question_id == "resp_1"
    assert questions[0].question_type == FeedbackQuestionType.RADIO
    assert len(questions[0].options) == 2
    assert questions[1].question_type == FeedbackQuestionType.TEXTAREA


def test_required_feedback_question_is_detected():
    html = """
    <div class="feedback_item">
      <label>Comment</label>
      <textarea name="resp_1" required></textarea>
    </div>
    """
    questions = MoodleFeedbackParser().parse(html)
    assert questions[0].required is True
