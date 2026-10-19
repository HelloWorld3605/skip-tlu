from __future__ import annotations

from bs4 import BeautifulSoup

from skiptlu.models.activity import Activity, CompletionStatus, ModuleType
from skiptlu.models.process import ActivityRestriction, RestrictionType


class RestrictionParser:
    """Conservative parser for Moodle's visible 'Not available unless' text."""

    def parse(self, activity: Activity, soup_or_text: BeautifulSoup | str) -> list[ActivityRestriction]:
        text = (
            soup_or_text.get_text(" ", strip=True)
            if isinstance(soup_or_text, BeautifulSoup)
            else soup_or_text
        )
        if "Not available unless" not in text:
            return []

        # Actual activity-id resolution belongs to discovery, where all course
        # activities are known. Keep this parser free of hard-coded IDs.
        return []

    def resolve_by_name(
        self,
        activity: Activity,
        source_activities: list[Activity],
        text: str,
    ) -> list[ActivityRestriction]:
        if "Not available unless" not in text:
            return []

        result: list[ActivityRestriction] = []
        lowered = text.lower()

        for source in source_activities:
            if source.id == activity.id:
                continue
            if source.name and source.name.lower() in lowered:
                result.append(
                    ActivityRestriction(
                        type=RestrictionType.COMPLETION,
                        source_activity_id=source.id,
                        source_activity_name=source.name,
                    )
                )
        return result
