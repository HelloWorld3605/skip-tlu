from skiptlu.models.activity import Activity, CompletionRequirement


class CompletionResolver:
    """Normalizes Moodle completion metadata into engine-level requirements."""

    def resolve(self, activity: Activity) -> list[CompletionRequirement]:
        if activity.requirements:
            return activity.requirements

        defaults = {
            "lesson": [CompletionRequirement(type="reach_end")],
            "quiz": [CompletionRequirement(type="attempt")],
            "assign": [CompletionRequirement(type="submission")],
            "feedback": [CompletionRequirement(type="response")],
            "resource": [CompletionRequirement(type="view")],
            "page": [CompletionRequirement(type="view")],
            "h5pactivity": [CompletionRequirement(type="interaction")],
        }
        return defaults.get(activity.module.value, [])
