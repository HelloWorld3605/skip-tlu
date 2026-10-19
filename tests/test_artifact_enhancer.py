import asyncio

from skiptlu.artifacts.enhancer import McpArtifactEnhancer
from skiptlu.models.artifact import Artifact, ArtifactKind


class FakeAdapter:
    def __init__(self):
        self.calls = []

    async def enhance(self, path, operations):
        self.calls.append((path, operations))
        return ["ok"]


class Planner:
    def __init__(self, operations):
        self.operations = operations

    def plan(self, specification):
        return self.operations


def test_mcp_artifact_enhancer_delegates_planned_operations(tmp_path):
    artifact = Artifact(path=tmp_path / "x.docx", kind=ArtifactKind.DOCX)
    artifact.path.write_bytes(b"not-a-real-docx")
    adapter = FakeAdapter()
    operations = [{"tool": "get_document_text", "arguments": {}}]
    enhancer = McpArtifactEnhancer(adapter, planner=Planner(operations))

    result = asyncio.run(enhancer.enhance(artifact, object()))

    assert result == artifact
    assert adapter.calls == [(artifact.path, operations)]


def test_mcp_artifact_enhancer_ignores_non_docx(tmp_path):
    artifact = Artifact(path=tmp_path / "x.txt", kind=ArtifactKind.EXISTING)
    artifact.path.write_text("x", encoding="utf-8")
    adapter = FakeAdapter()
    enhancer = McpArtifactEnhancer(
        adapter,
        planner=Planner([{"tool": "noop", "arguments": {}}]),
    )

    result = asyncio.run(enhancer.enhance(artifact, object()))

    assert result == artifact
    assert adapter.calls == []
