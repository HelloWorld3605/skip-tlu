import pytest

from skiptlu.artifacts.mcp_planner import McpOperationPlanner
from skiptlu.tasks.specification import ArtifactType, PracticalTaskSpecification


def test_mcp_planner_is_empty_by_default():
    spec = PracticalTaskSpecification(
        activity_id=1,
        title="demo",
        artifact_type=ArtifactType.DOCX,
    )

    assert McpOperationPlanner().plan(spec) == []


def test_mcp_planner_reads_explicit_operations():
    spec = PracticalTaskSpecification(
        activity_id=1,
        title="demo",
        artifact_type=ArtifactType.DOCX,
        metadata={
            "mcp_operations": [
                {
                    "tool": "search_and_replace",
                    "arguments": {
                        "old_text": "foo",
                        "new_text": "bar",
                    },
                }
            ]
        },
    )

    assert McpOperationPlanner().plan(spec) == [
        {
            "tool": "search_and_replace",
            "arguments": {
                "old_text": "foo",
                "new_text": "bar",
            },
        }
    ]


def test_mcp_planner_rejects_invalid_operation():
    spec = PracticalTaskSpecification(
        activity_id=1,
        title="demo",
        artifact_type=ArtifactType.DOCX,
        metadata={"mcp_operations": [{"tool": "x", "arguments": "bad"}]},
    )

    with pytest.raises(ValueError, match="arguments"):
        McpOperationPlanner().plan(spec)
