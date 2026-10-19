from skiptlu.course.discovery import CourseDiscovery
from skiptlu.models.activity import CompletionStatus, ModuleType
from skiptlu.models.process import RestrictionType


HTML = """
<html>
  <head><title>Week 11 - Excel</title></head>
  <body>
    <li class="activity activity-item">
      <a href="/mod/lesson/view.php?id=1101">
        <span class="instancename">[LÝ THUYẾT] LÀM QUEN VỚI EXCEL 365</span>
      </a>
      <div class="completion-info">
        <span>Done</span>
      </div>
    </li>

    <li class="activity activity-item">
      <a href="/mod/assign/view.php?id=1102">
        <span class="instancename">[NỘP BÀI TẬP] LÀM QUEN EXCEL 365</span>
      </a>
      <div class="availabilityinfo">
        Not available unless:
        <strong>[LÝ THUYẾT] LÀM QUEN VỚI EXCEL 365</strong>
      </div>
      <div class="completion-info">
        <span>Make a submission</span>
      </div>
    </li>

    <li class="activity activity-item">
      <a href="/mod/quiz/view.php?id=1103">
        <span class="instancename">[LUYỆN TẬP TRẮC NGHIỆM] EXCEL 365</span>
      </a>
      <div class="completion-info">
        <span>Receive a grade</span>
        <span>Receive a passing grade</span>
      </div>
      <div class="activity-dates">
        Opened: 01 January 2030, 08:00
        Closed: 31 January 2030, 23:59
      </div>
    </li>

    <li class="activity activity-item">
      <a href="/mod/lesson/view.php?id=1104">
        <span class="instancename">[THỰC HÀNH] Định dạng Excel</span>
      </a>
      <button>Mark as done</button>
    </li>
  </body>
</html>
"""


def test_discovery_parses_activity_type_and_completion():
    course = CourseDiscovery(None).parse_html(
        HTML,
        course_id=1,
        name="Week 11",
        base_url="https://elearning.example.edu/course/view.php?id=1",
    )

    assert len(course.activities) == 4
    lesson = course.activities[0]
    assert lesson.module == ModuleType.LESSON
    assert lesson.completion_status == CompletionStatus.COMPLETE
    assert lesson.url.endswith("/mod/lesson/view.php?id=1101")


def test_discovery_resolves_completion_restriction_after_all_activities_are_known():
    course = CourseDiscovery(None).parse_html(
        HTML,
        course_id=1,
        name="Week 11",
    )

    assignment = course.activities[1]
    assert len(assignment.restrictions) == 1
    restriction = assignment.restrictions[0]
    assert restriction.type == RestrictionType.COMPLETION
    assert restriction.source_activity_id == 1101
    assert restriction.required_status == "complete"


def test_discovery_parses_real_completion_requirements():
    course = CourseDiscovery(None).parse_html(
        HTML,
        course_id=1,
        name="Week 11",
    )

    assignment = course.activities[1]
    assert {item.type for item in assignment.requirements} >= {"submission"}

    quiz = course.activities[2]
    assert {item.type for item in quiz.requirements} >= {
        "grade",
        "passing_grade",
    }


def test_discovery_parses_manual_mark_done():
    course = CourseDiscovery(None).parse_html(
        HTML,
        course_id=1,
        name="Week 11",
    )

    practical = course.activities[3]
    assert practical.metadata["manual_mark_done"] is True


def test_discovery_parses_time_window_when_format_is_supported():
    course = CourseDiscovery(None).parse_html(
        HTML,
        course_id=1,
        name="Week 11",
    )

    quiz = course.activities[2]
    assert quiz.metadata["opens_at"].year == 2030
    assert quiz.metadata["closes_at"].year == 2030


COURSE_HTML = """
<html><body>
<li id="section-17907" class="section">
  <h3 class="sectionname">Week 1</h3>
  <li class="activity activity-item">
    <a href="/mod/lesson/view.php?id=101"><span class="instancename">Lesson A</span></a>
  </li>
</li>
<li id="section-17910" class="section">
  <h3 class="sectionname">Week 2</h3>
  <li class="activity activity-item">
    <a href="/mod/quiz/view.php?id=102"><span class="instancename">Quiz B</span></a>
  </li>
</li>
</body></html>
"""


def test_discovery_parses_full_course_sections():
    course = CourseDiscovery(None).parse_course_html(
        COURSE_HTML,
        course_id=42,
        name="ELE1101",
        base_url="https://elearning.example.edu/course/view.php?id=42",
    )

    assert [section.id for section in course.sections] == [17907, 17910]
    assert [section.name for section in course.sections] == ["Week 1", "Week 2"]
    assert [activity.id for activity in course.activities] == [101, 102]


ELMS_TLU_COURSE_INDEX_HTML = """
<html><body>
<nav id="courseindex">
  <div id="course-index-section-17907" class="courseindex-section" role="treeitem">
    <a class="courseindex-link" href="/course/section.php?id=17907">Tuần 1. Sử dụng máy tính cơ bản</a>
    <div class="courseindex-item-content">
      <ul class="courseindex-sectioncontent">
        <li class="courseindex-item" id="course-index-cm-50883">
          <span class="completioninfo completion_complete" data-value="2"></span>
          <a class="courseindex-link" href="/mod/lesson/view.php?id=50883">GIỚI THIỆU MÔN HỌC</a>
        </li>
        <li class="courseindex-item" id="course-index-cm-51540">
          <span class="completioninfo completion_complete" data-value="1"></span>
          <a class="courseindex-link" href="/mod/quiz/view.php?id=51540">2627.K1.KIỂM TRA TRẮC NGHIỆM TUẦN 1</a>
        </li>
      </ul>
    </div>
  </div>
  <div id="course-index-section-17910" class="courseindex-section" role="treeitem">
    <a class="courseindex-link" href="/course/section.php?id=17910">Tuần 2. Làm quen với Word</a>
    <div class="courseindex-item-content">
      <ul class="courseindex-sectioncontent">
        <li class="courseindex-item" id="course-index-cm-51543">
          <span class="completioninfo completion_incomplete" data-value="0"></span>
          <a class="courseindex-link" href="/mod/quiz/view.php?id=51543">2627.K1.KIỂM TRA TRẮC NGHIỆM TUẦN 2</a>
        </li>
      </ul>
    </div>
  </div>
</nav>
</body></html>
"""


def test_discovery_parses_elms_tlu_courseindex_sections_and_completion():
    course = CourseDiscovery(None).parse_course_html(
        ELMS_TLU_COURSE_INDEX_HTML,
        course_id=23946,
        name="ELE1101: Năng lực số và Công nghệ văn phòng",
        base_url="https://elearning.thanglong.edu.vn/course/view.php?id=23946",
    )

    assert [section.id for section in course.sections] == [17907, 17910]
    assert [section.name for section in course.sections] == [
        "Tuần 1. Sử dụng máy tính cơ bản",
        "Tuần 2. Làm quen với Word",
    ]
    assert [activity.id for activity in course.activities] == [50883, 51540, 51543]
    assert course.activities[0].completion_status == CompletionStatus.COMPLETE
    assert course.activities[1].completion_status == CompletionStatus.COMPLETE
    assert course.activities[2].completion_status == CompletionStatus.INCOMPLETE
