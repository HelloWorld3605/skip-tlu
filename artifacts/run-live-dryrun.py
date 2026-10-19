import html
import json
from pathlib import Path

from skiptlu.course.discovery import CourseDiscovery
from skiptlu.completion.planner import ProcessPlanner
from skiptlu.completion.execution_planner import ExecutionPlanner

records = json.loads(Path("artifacts/live-course-23946-records.json").read_text(encoding="utf-8"))

sections = {}
for item in records["activities"]:
    sid = item["sectionId"] or "0"
    sections.setdefault(sid, {"name": item["sectionName"] or "Other", "items": []})
    sections[sid]["items"].append(item)

parts = [
    "<html><head><title>ELE1101: Năng lực số và Công nghệ văn phòng</title></head><body>"
]
for sid, section in sections.items():
    parts.append(
        f'<div id="course-index-section-{html.escape(str(sid))}" class="courseindex-section">'
        f'<a class="courseindex-link" href="/course/section.php?id={html.escape(str(sid))}">{html.escape(section["name"])}</a>'
        '<ul class="courseindex-sectioncontent">'
    )
    for item in section["items"]:
        marker = (
            f'<span class="completioninfo {html.escape(item["completionClass"])}" '
            f'data-value="{html.escape(str(item["completionValue"] or ""))}"></span>'
        )
        parts.append(
            f'<li class="courseindex-item">{marker}'
            f'<a class="courseindex-link" href="{html.escape(item["url"])}">{html.escape(item["name"])}</a>'
            '</li>'
        )
    parts.append("</ul></div>")
parts.append("</body></html>")

course = CourseDiscovery(None).parse_course_html(
    "".join(parts),
    course_id=records["courseId"],
    name="ELE1101: Năng lực số và Công nghệ văn phòng",
    base_url="https://elearning.thanglong.edu.vn/course/view.php?id=23946",
)

planner = ProcessPlanner()
snapshot = planner.snapshot(course.activities)
execution = ExecutionPlanner().build(course.activities)

by_module = {}
by_status = {}
for activity in course.activities:
    by_module[activity.module.value] = by_module.get(activity.module.value, 0) + 1
    by_status[activity.completion_status.value] = by_status.get(activity.completion_status.value, 0) + 1

states = {}
for state in snapshot.states.values():
    states[state.availability.value] = states.get(state.availability.value, 0) + 1

print(json.dumps({
    "course": {"id": course.id, "name": course.name},
    "sections": [{"id": s.id, "name": s.name, "activities": len(s.activities)} for s in course.sections],
    "activity_count": len(course.activities),
    "by_module": by_module,
    "by_completion": by_status,
    "availability": states,
    "execution_order_count": len(execution.ordered_activity_ids),
    "execution_order_first_20": list(execution.ordered_activity_ids[:20]),
    "cycles": [list(c) for c in execution.cycles],
}, ensure_ascii=False, indent=2))
