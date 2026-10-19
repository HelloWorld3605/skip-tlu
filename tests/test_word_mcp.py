import asyncio
from pathlib import Path

import pytest

from skiptlu.artifacts.word_mcp import (
    McpToolCapability,
    McpWordAdapter,
    McpWordServerConfig,
)


class FakeMcpClient:
    def __init__(self):
        self.calls = []
        self.tools = []

    async def call_tool(self, tool_name, arguments=None):
        self.calls.append((tool_name, dict(arguments or {})))
        return {"tool": tool_name, "arguments": dict(arguments or {})}

    async def list_tools(self):
        return {"tools": self.tools}


def test_mcp_word_adapter_confines_paths(tmp_path):
    adapter = McpWordAdapter(
        McpWordServerConfig(command="python", allowed_root=tmp_path)
    )

    inside = tmp_path / "generated.docx"
    assert adapter.resolve_path(inside) == inside.resolve()

    outside = tmp_path.parent / "outside.docx"
    with pytest.raises(ValueError, match="escapes allowed root"):
        adapter.resolve_path(outside)


def test_mcp_word_adapter_can_use_injected_client(tmp_path):
    client = FakeMcpClient()
    adapter = McpWordAdapter(
        McpWordServerConfig(command="python", allowed_root=tmp_path),
        client=client,
    )

    source = tmp_path / "template.docx"
    target = tmp_path / "generated.docx"

    result = asyncio.run(adapter.copy_document(source, target))

    assert result["tool"] == "copy_document"
    assert client.calls == [
        (
            "copy_document",
            {
                "source_filename": str(source.resolve()),
                "destination_filename": str(target.resolve()),
            },
        )
    ]


def test_mcp_word_adapter_discovers_capabilities(tmp_path):
    client = FakeMcpClient()
    client.tools = [
        McpToolCapability(
            name="copy_document",
            description="Copy a Word document",
            input_schema={"type": "object"},
        ),
        {"name": "get_document_text", "description": "Read text"},
    ]
    adapter = McpWordAdapter(
        McpWordServerConfig(command="python", allowed_root=tmp_path),
        client=client,
    )

    capabilities = asyncio.run(adapter.list_tools())

    assert capabilities == [
        client.tools[0],
        McpToolCapability(name="get_document_text", description="Read text"),
    ]


def test_mcp_word_adapter_require_tools_rejects_missing(tmp_path):
    client = FakeMcpClient()
    client.tools = [{"name": "copy_document"}]
    adapter = McpWordAdapter(
        McpWordServerConfig(command="python", allowed_root=tmp_path),
        client=client,
    )

    with pytest.raises(RuntimeError, match="get_document_text"):
        asyncio.run(adapter.require_tools("copy_document", "get_document_text"))


def test_mcp_word_adapter_require_tools_accepts_available(tmp_path):
    client = FakeMcpClient()
    client.tools = [{"name": "copy_document"}, {"name": "get_document_text"}]
    adapter = McpWordAdapter(
        McpWordServerConfig(command="python", allowed_root=tmp_path),
        client=client,
    )

    asyncio.run(adapter.require_tools("copy_document", "get_document_text"))


def test_mcp_word_adapter_enhance_executes_explicit_operations(tmp_path):
    client = FakeMcpClient()
    adapter = McpWordAdapter(
        McpWordServerConfig(command="python", allowed_root=tmp_path),
        client=client,
    )

    path = tmp_path / "generated.docx"
    results = asyncio.run(
        adapter.enhance(
            path,
            [
                {"tool": "get_document_text"},
                {"tool": "custom_tool", "arguments": {"value": "x"}},
            ],
        )
    )

    assert len(results) == 2
    assert client.calls[0] == (
        "get_document_text",
        {"filename": str(path.resolve())},
    )
    assert client.calls[1] == (
        "custom_tool",
        {"value": "x", "filename": str(path.resolve())},
    )
