import asyncio

from skiptlu.completion.verification import VerificationEngine
from skiptlu.client.session import AssignmentSubmission
from skiptlu.models.activity import Activity, CompletionStatus, ModuleType


class FakeSession:
    def __init__(self, status=CompletionStatus.COMPLETE):
        self.status = status
        self.calls = []

    async def read_completion(self, activity):
        self.calls.append(("completion", activity.id))
        return self.status

    async def read_assignment_submission(self, activity):
        self.calls.append(("assignment", activity.id))
        return AssignmentSubmission(
            activity.id,
            True,
            ("submission.docx",),
            "Submitted for grading",
            self.status,
        )


def test_verification_engine_reads_generic_moodle_completion():
    async def run():
        session = FakeSession()
        verifier = VerificationEngine(session)
        activity = Activity(
            id=51014,
            module=ModuleType.LESSON,
            name="Lesson",
        )

        result = await verifier.verify(activity)

        assert result.status == CompletionStatus.COMPLETE
        assert result.evidence["source"] == "moodle_completion_marker"
        assert session.calls == [("completion", 51014)]

    asyncio.run(run())


def test_verification_engine_reads_assignment_submission_evidence():
    async def run():
        session = FakeSession(CompletionStatus.COMPLETE)
        verifier = VerificationEngine(session)
        activity = Activity(
            id=51068,
            module=ModuleType.ASSIGNMENT,
            name="Assignment",
        )

        result = await verifier.verify(activity)

        assert result.status == CompletionStatus.COMPLETE
        assert result.evidence["has_submission"] is True
        assert result.evidence["files"] == ["submission.docx"]
        assert session.calls == [("assignment", 51068)]

    asyncio.run(run())
