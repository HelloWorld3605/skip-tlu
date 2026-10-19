import asyncio

from skiptlu.client.session import AssignmentSubmission
from skiptlu.handlers.practical import AssignmentHandler
from skiptlu.models.activity import Activity, CompletionStatus, ModuleType


class FakeAssignmentSession:
    def __init__(self, completion=CompletionStatus.COMPLETE):
        self.completion = completion
        self.submitted = False
        self.path = None

    async def submit_assignment(self, activity, artifact_path):
        self.submitted = True
        self.path = artifact_path
        return AssignmentSubmission(activity.id, True, (artifact_path.name,), "Submitted for grading", self.completion)

    async def read_assignment_submission(self, activity):
        return AssignmentSubmission(
            activity.id, self.submitted,
            (self.path.name,) if self.path else (),
            "Submitted for grading" if self.submitted else "",
            self.completion if self.submitted else CompletionStatus.INCOMPLETE,
        )


def test_assignment_handler_requires_non_empty_artifact(tmp_path):
    async def run():
        session = FakeAssignmentSession()
        handler = AssignmentHandler(session)
        activity = Activity(id=51068, module=ModuleType.ASSIGNMENT, name="week4")
        empty = tmp_path / "empty.docx"
        empty.write_bytes(b"")
        status = await handler.execute(activity, empty)
        assert status == CompletionStatus.INCOMPLETE
        assert not session.submitted

    asyncio.run(run())


def test_assignment_handler_submits_and_verifies(tmp_path):
    async def run():
        session = FakeAssignmentSession()
        handler = AssignmentHandler(session)
        activity = Activity(id=51068, module=ModuleType.ASSIGNMENT, name="week4")
        artifact = tmp_path / "A00001_TEST_LuyenTap_BaiSo1.docx"
        artifact.write_bytes(b"real-test-artifact")

        status = await handler.execute(activity, artifact)
        assert status == CompletionStatus.COMPLETE
        assert session.submitted
        assert handler.last_execution is not None
        assert handler.last_execution.submission_submitted

        verified = await handler.verify(activity)
        assert verified == CompletionStatus.COMPLETE

    asyncio.run(run())
