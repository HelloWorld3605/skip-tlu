from skiptlu.quiz.models import QuestionType
from skiptlu.quiz.parser import MoodleQuizParser


def test_parse_single_choice():
    html = """
    <div class="que multichoice" id="question-42">
      <div class="qtext">Which format is a document?</div>
      <div class="answer">
        <input type="radio" id="q42a" name="q42" value="1">
        <label for="q42a">DOCX</label>
        <input type="radio" id="q42b" name="q42" value="2">
        <label for="q42b">PNG</label>
      </div>
    </div>
    """
    questions = MoodleQuizParser().parse(html)
    assert len(questions) == 1
    assert questions[0].question_id == "42"
    assert questions[0].question_type == QuestionType.SINGLE_CHOICE
    assert [x.label for x in questions[0].options] == ["DOCX", "PNG"]


def test_parse_multiple_choice():
    html = """
    <div class="que multichoice" id="question-7">
      <div class="qtext">Select formats.</div>
      <input type="checkbox" id="q7a" value="docx"><label for="q7a">DOCX</label>
      <input type="checkbox" id="q7b" value="pdf"><label for="q7b">PDF</label>
    </div>
    """
    questions = MoodleQuizParser().parse(html)
    assert questions[0].question_type == QuestionType.MULTIPLE_CHOICE
    assert len(questions[0].options) == 2


def test_parse_text_question():
    html = """
    <div class="que shortanswer" id="question-9">
      <div class="qtext">Enter your name.</div>
      <input type="text" name="q9">
    </div>
    """
    questions = MoodleQuizParser().parse(html)
    assert questions[0].question_type == QuestionType.TEXT
