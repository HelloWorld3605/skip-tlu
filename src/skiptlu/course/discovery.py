from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from skiptlu.client.moodle import MoodleClient
from skiptlu.models.activity import (
    Activity,
    CompletionRequirement,
    CompletionStatus,
    ModuleType,
)
from skiptlu.models.course import Course, CourseSection
from skiptlu.models.process import ActivityRestriction, RestrictionType


SUPPORTED_MODULES = {item.value for item in ModuleType}

_DATE_PATTERNS = (
    re.compile(r"Opened:\s*(.+?)(?=\s+(?:Closed|Due):|$)", re.I),
    re.compile(r"Opened from:\s*(.+?)(?=\s+(?:Closed|Due):|$)", re.I),
    re.compile(r"Closed:\s*(.+?)(?=\s+(?:Opened|Due):|$)", re.I),
    re.compile(r"Due:\s*(.+?)(?=\s+(?:Opened|Closed):|$)", re.I),
)


class CourseDiscovery:
    """Discover Moodle activities and the state needed by ProcessPlanner.

    The parser intentionally works from server-rendered Moodle HTML. It does not
    infer completion from a successful click; completion is read from Moodle's
    authoritative activity/course UI.
    """

    def __init__(self, client: MoodleClient):
        self.client = client

    def parse_course_html(
        self,
        html: str,
        *,
        course_id: int,
        name: str = "",
        base_url: str = "",
    ) -> Course:
        """Parse a full Moodle course page into ordered sections and activities."""
        soup = BeautifulSoup(html, "html.parser")
        course = self.parse_html(
            html,
            course_id=course_id,
            name=name,
            base_url=base_url,
        )
        all_activities = course.activities

        # Map each discovered activity to its nearest Moodle section container.
        by_url = {activity.url: activity for activity in all_activities if activity.url}
        section_buckets: list[tuple[int | None, str, list[Activity]]] = []

        section_nodes = soup.select(
            'li[id^="section-"], li.section, .course-section, .section.main, div.courseindex-section'
        )

        if not section_nodes:
            return course

        seen_activity_ids: set[int] = set()
        for index, node in enumerate(section_nodes):
            section_id = self._section_id(node)
            section_name = self._section_name(node, index + 1)
            bucket: list[Activity] = []

            for anchor in node.select('a[href*="/mod/"][href*="view.php?id="]'):
                href = anchor.get("href")
                if not isinstance(href, str):
                    continue
                url = urljoin(base_url, href)
                activity = by_url.get(url)
                if activity is None or activity.id in seen_activity_ids:
                    continue
                seen_activity_ids.add(activity.id)
                bucket.append(activity)

            if bucket:
                section_buckets.append((section_id, section_name, bucket))

        # Some themes render activities outside the conventional section node.
        # Preserve them in a synthetic section rather than silently dropping them.
        leftovers = [
            activity for activity in all_activities
            if activity.id not in seen_activity_ids
        ]
        if leftovers:
            section_buckets.append((None, "Other", leftovers))

        if not section_buckets:
            return course

        return Course(
            id=course_id,
            name=name or course.name,
            sections=[
                CourseSection(id=section_id, name=section_name, activities=activities)
                for section_id, section_name, activities in section_buckets
            ],
        )

    @staticmethod
    def _section_id(node: Tag) -> int | None:
        raw = node.get("data-sectionid")
        if raw is None:
            raw = node.get("id")
            if isinstance(raw, str):
                match = re.search(r"(?:course-index-section-|section-|section)(\d+)", raw)
                if match:
                    raw = match.group(1)
        try:
            return int(raw) if raw is not None else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _section_name(node: Tag, fallback_index: int) -> str:
        heading = node.select_one(
            '.sectionname, .sectionname a, h2.sectionname, h3.sectionname, .course-section-header, a.courseindex-link[href*="/course/section.php"]'
        )
        if heading:
            value = heading.get_text(" ", strip=True)
            if value:
                return value
        return f"Section {fallback_index}"

    async def section(
        self,
        section_url: str,
        course_id: int,
        name: str = "",
        section_id: int | None = None,
    ) -> Course:
        response = await self.client.get(section_url)
        response.raise_for_status()
        return self.parse_html(
            response.text,
            course_id=course_id,
            name=name,
            base_url=section_url,
            section_id=section_id,
        )

    def parse_html(
        self,
        html: str,
        *,
        course_id: int,
        name: str = "",
        base_url: str = "",
        section_id: int | None = None,
    ) -> Course:
        soup = BeautifulSoup(html, "html.parser")
        activities: list[Activity] = []

        anchors = soup.select('a[href*="/mod/"][href*="view.php?id="]')
        seen: set[tuple[str, int]] = set()

        for anchor in anchors:
            parsed = self._parse_activity_anchor(anchor, base_url)
            if parsed is None:
                continue

            module, activity_id, cmid, url = parsed
            key = (module.value, activity_id)
            if key in seen:
                continue
            seen.add(key)

            container = self._activity_container(anchor)
            title = self._activity_title(anchor)
            if not title:
                continue

            activities.append(
                self._build_activity(
                    anchor=anchor,
                    container=container,
                    module=module,
                    activity_id=activity_id,
                    cmid=cmid,
                    title=title,
                    url=url,
                    all_known_names=[],
                )
            )

        # Resolve completion restrictions only after every activity is known.
        names = [activity.name for activity in activities]
        for activity in activities:
            container_text = str(activity.metadata.pop("_restriction_text", ""))
            if container_text:
                activity.metadata["restrictions"] = self._resolve_restrictions(
                    activity,
                    activities,
                    container_text,
                )

        course_name = name
        if not course_name:
            course_name = soup.title.get_text(" ", strip=True) if soup.title else str(course_id)

        return Course(
            id=course_id,
            name=course_name,
            sections=[
                CourseSection(
                    id=section_id,
                    name=name or "current",
                    activities=activities,
                )
            ],
        )

    def _build_activity(
        self,
        *,
        anchor: Tag,
        container: Tag,
        module: ModuleType,
        activity_id: int,
        cmid: int | None,
        title: str,
        url: str,
        all_known_names: list[str],
    ) -> Activity:
        container_text = container.get_text(" ", strip=True)
        anchor_text = anchor.get_text(" ", strip=True)
        status = self._completion_status(container)
        requirements = self._completion_requirements(container, module)
        metadata: dict[str, object] = {
            "source": "moodle_html",
            "activity_text": container_text,
        }

        restriction_text = self._restriction_text(container)
        if restriction_text:
            metadata["_restriction_text"] = restriction_text

        windows = self._time_windows(container)
        metadata.update(windows)

        if self._has_manual_mark_done(container):
            metadata["manual_mark_done"] = True

        if anchor_text:
            metadata["anchor_text"] = anchor_text

        return Activity(
            id=activity_id,
            cmid=cmid,
            module=module,
            name=title,
            url=url,
            completion_status=status,
            requirements=requirements,
            metadata=metadata,
        )

    @staticmethod
    def _parse_activity_anchor(
        anchor: Tag,
        base_url: str,
    ) -> tuple[ModuleType, int, int | None, str] | None:
        href = anchor.get("href")
        if not isinstance(href, str):
            return None

        parsed_url = urlparse(urljoin(base_url, href))
        match = re.search(r"/mod/([^/]+)/view.php$", parsed_url.path)
        if not match:
            return None

        module_name = match.group(1)
        if module_name not in SUPPORTED_MODULES:
            return None

        query = parse_qs(parsed_url.query)
        try:
            activity_id = int(query["id"][0])
        except (KeyError, ValueError, IndexError):
            return None

        cmid = None
        if "cmid" in query:
            try:
                cmid = int(query["cmid"][0])
            except (ValueError, IndexError):
                pass

        return ModuleType(module_name), activity_id, cmid, parsed_url.geturl()

    @staticmethod
    def _activity_container(anchor: Tag) -> Tag:
        # Moodle normally renders each activity inside an element carrying one
        # of these classes. Prefer the smallest meaningful activity wrapper.
        for parent in anchor.parents:
            if not isinstance(parent, Tag):
                continue
            classes = set(parent.get("class", []))
            if classes.intersection(
                {
                    "activity",
                    "activity-item",
                    "mod-indent-outer",
                    "activityinstance",
                    "courseindex-item",
                }
            ):
                return parent
        return anchor.parent if isinstance(anchor.parent, Tag) else anchor

    @staticmethod
    def _activity_title(anchor: Tag) -> str:
        title_node = anchor.select_one(".instancename")
        if title_node:
            return title_node.get_text(" ", strip=True)
        return anchor.get_text(" ", strip=True)

    @staticmethod
    def _completion_status(container: Tag) -> CompletionStatus:
        text = container.get_text(" ", strip=True).lower()

        if any(
            marker in text
            for marker in (
                "completed",
                "complete",
                "done",
                "passed",
                "đã hoàn thành",
                "hoàn thành",
            )
        ) and not any(
            marker in text
            for marker in (
                "not completed",
                "not complete",
                "incomplete",
                "chưa hoàn thành",
                "chưa hoàn tất",
            )
        ):
            if "passed" in text or "đạt" in text:
                return CompletionStatus.PASSED
            return CompletionStatus.COMPLETE

        if any(
            marker in text
            for marker in (
                "not completed",
                "not complete",
                "incomplete",
                "chưa hoàn thành",
                "chưa hoàn tất",
            )
        ):
            return CompletionStatus.INCOMPLETE

        # Moodle themes such as ELMS-TLU expose authoritative state on a
        # descendant completion marker rather than as text on the activity item.
        marker = container.select_one(".completioninfo, .rui-completion-info")
        if marker is not None:
            marker_classes = " ".join(marker.get("class", []))
            if "completion_complete" in marker_classes:
                return CompletionStatus.COMPLETE
            if "completion_incomplete" in marker_classes:
                return CompletionStatus.INCOMPLETE
            value = marker.get("data-value")
            if value not in (None, "", "NaN"):
                try:
                    return (
                        CompletionStatus.COMPLETE
                        if float(value) > 0
                        else CompletionStatus.INCOMPLETE
                    )
                except ValueError:
                    pass

        classes = " ".join(container.get("class", []))
        if "complete" in classes:
            return CompletionStatus.COMPLETE

        return CompletionStatus.UNKNOWN

    @staticmethod
    def _completion_requirements(
        container: Tag,
        module: ModuleType,
    ) -> list[CompletionRequirement]:
        text = container.get_text(" ", strip=True).lower()
        requirements: list[CompletionRequirement] = []

        manual = CourseDiscovery._has_manual_mark_done(container)
        if manual:
            requirements.append(
                CompletionRequirement(type="manual_mark_done")
            )

        patterns: tuple[tuple[str, tuple[str, ...]], ...] = (
            ("submission", ("make a submission", "nộp bài")),
            ("attempt", ("make attempts", "make an attempt", "thực hiện bài", "làm bài")),
            ("grade", ("receive a grade", "nhận điểm")),
            ("passing_grade", ("receive a passing grade", "đạt điểm đỗ", "đạt điểm")),
            ("view", ("view", "xem")),
        )

        for requirement_type, markers in patterns:
            if any(marker in text for marker in markers):
                if not any(item.type == requirement_type for item in requirements):
                    requirements.append(
                        CompletionRequirement(type=requirement_type)
                    )

        if not requirements:
            defaults = {
                ModuleType.LESSON: "reach_end",
                ModuleType.ASSIGNMENT: "submission",
                ModuleType.QUIZ: "attempt",
                ModuleType.FEEDBACK: "response",
                ModuleType.RESOURCE: "view",
                ModuleType.PAGE: "view",
                ModuleType.H5P: "interaction",
            }
            if module in defaults:
                requirements.append(
                    CompletionRequirement(
                        type=defaults[module],
                        metadata={"inferred": True},
                    )
                )

        return requirements

    @staticmethod
    def _restriction_text(container: Tag) -> str:
        nodes = container.select(
            ".availabilityinfo, .availability-info, .restriction, .availability"
        )
        text_parts = [
            node.get_text(" ", strip=True)
            for node in nodes
            if node.get_text(" ", strip=True)
        ]
        if text_parts:
            return " ".join(text_parts)

        text = container.get_text(" ", strip=True)
        for marker in ("Not available unless:", "Not available unless", "Không khả dụng trừ khi"):
            if marker.lower() in text.lower():
                return text
        return ""

    @staticmethod
    def _resolve_restrictions(
        activity: Activity,
        activities: list[Activity],
        text: str,
    ) -> list[ActivityRestriction]:
        lowered = text.lower()
        result: list[ActivityRestriction] = []

        for source in activities:
            if source.id == activity.id or not source.name:
                continue
            if source.name.lower() not in lowered:
                continue

            restriction_type = RestrictionType.COMPLETION
            required_status = "complete"
            if "passing grade" in lowered or "đạt điểm" in lowered:
                restriction_type = RestrictionType.GRADE
                required_status = "passed"

            result.append(
                ActivityRestriction(
                    type=restriction_type,
                    source_activity_id=source.id,
                    source_activity_name=source.name,
                    required_status=required_status,
                    metadata={"raw_text": text},
                )
            )

        return result

    @staticmethod
    def _has_manual_mark_done(container: Tag) -> bool:
        text = container.get_text(" ", strip=True).lower()
        if "mark as done" in text or "đánh dấu là hoàn thành" in text:
            return True

        for node in container.select(
            "button, input[type=submit], a[role=button]"
        ):
            label = " ".join(
                filter(
                    None,
                    [
                        node.get_text(" ", strip=True),
                        node.get("value"),
                        node.get("aria-label"),
                        node.get("title"),
                    ],
                )
            ).lower()
            if "mark as done" in label or "đánh dấu là hoàn thành" in label:
                return True

        return False

    @staticmethod
    def _time_windows(container: Tag) -> dict[str, object]:
        result: dict[str, object] = {}
        text = container.get_text(" ", strip=True)

        for pattern in _DATE_PATTERNS:
            match = pattern.search(text)
            if not match:
                continue

            label = pattern.pattern.split(":")[0].split("\\s")[-1].lower()
            raw_value = match.group(1).strip()
            parsed = CourseDiscovery._parse_datetime(raw_value)
            if parsed is not None:
                if label == "opened":
                    result["opens_at"] = parsed
                elif label == "closed":
                    result["closes_at"] = parsed
                elif label == "due":
                    result["due_at"] = parsed

        return result

    @staticmethod
    def _parse_datetime(value: str) -> datetime | None:
        # Moodle installations differ in locale/format. Keep parsing
        # conservative; the raw activity text remains available for a future
        # locale-aware adapter.
        value = value.strip()
        for fmt in (
            "%d %B %Y, %H:%M",
            "%d %B %Y %H:%M",
            "%d/%m/%Y %H:%M",
            "%Y-%m-%d %H:%M",
        ):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None
