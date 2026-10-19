from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class McpWordServerConfig:
    """Configuration for an external Word MCP server."""

    command: str
    args: tuple[str, ...] = ()
    cwd: Path | None = None
    allowed_root: Path | None = None


@dataclass(frozen=True)
class McpToolCapability:
    """A discovered MCP tool capability."""

    name: str
    description: str = ""
    input_schema: Mapping[str, Any] | None = None


class WordMcpClient(Protocol):
    async def call_tool(self, tool_name: str, arguments: Mapping[str, Any] | None = None) -> Any: ...
    async def list_tools(self) -> Any: ...


class McpWordAdapter:
    """Optional Word-MCP integration."""

    name = "mcp"

    def __init__(self, config: McpWordServerConfig, *, client: WordMcpClient | None = None):
        self.config = config
        self._client = client

    def resolve_path(self, path: Path) -> Path:
        resolved = path.resolve()
        root = self.config.allowed_root
        if root is None:
            return resolved
        root = root.resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"Word MCP path escapes allowed root: {resolved}") from exc
        return resolved

    async def _with_stdio_client(self, operation):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(
            command=self.config.command,
            args=list(self.config.args),
            cwd=str(self.config.cwd) if self.config.cwd else None,
        )
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                return await operation(session)

    async def call_tool(self, tool_name: str, arguments: Mapping[str, Any] | None = None) -> Any:
        if self._client is not None:
            return await self._client.call_tool(tool_name, arguments)

        async def invoke(session):
            return await session.call_tool(tool_name, dict(arguments or {}))

        return await self._with_stdio_client(invoke)

    @staticmethod
    def _normalize_tools(result: Any) -> list[McpToolCapability]:
        if isinstance(result, Mapping):
            tools = result.get("tools", [])
        else:
            tools = getattr(result, "tools", result)
        if tools is None:
            return []

        capabilities: list[McpToolCapability] = []
        for tool in tools:
            if isinstance(tool, Mapping):
                name = str(tool.get("name", ""))
                description = str(tool.get("description", "") or "")
                schema = tool.get("inputSchema")
            else:
                name = str(getattr(tool, "name", ""))
                description = str(getattr(tool, "description", "") or "")
                schema = getattr(tool, "inputSchema", getattr(tool, "input_schema", None))

            if name:
                capabilities.append(
                    McpToolCapability(name=name, description=description, input_schema=schema)
                )
        return capabilities

    async def list_tools(self) -> list[McpToolCapability]:
        if self._client is not None:
            result = await self._client.list_tools()
        else:
            async def discover(session):
                return await session.list_tools()
            result = await self._with_stdio_client(discover)
        return self._normalize_tools(result)

    async def require_tools(self, *names: str) -> None:
        available = {tool.name for tool in await self.list_tools()}
        missing = [name for name in names if name not in available]
        if missing:
            raise RuntimeError("Word MCP server is missing required tools: " + ", ".join(missing))

    async def copy_document(self, source: Path, destination: Path) -> Any:
        source = self.resolve_path(source)
        destination = self.resolve_path(destination)
        return await self.call_tool(
            "copy_document",
            {"source_filename": str(source), "destination_filename": str(destination)},
        )

    async def get_document_text(self, path: Path) -> Any:
        path = self.resolve_path(path)
        return await self.call_tool("get_document_text", {"filename": str(path)})

    async def enhance(self, path: Path, operations: list[Mapping[str, Any]]) -> list[Any]:
        path = self.resolve_path(path)
        results: list[Any] = []
        for operation in operations:
            tool_name = str(operation["tool"])
            arguments = dict(operation.get("arguments", {}))
            arguments.setdefault("filename", str(path))
            results.append(await self.call_tool(tool_name, arguments))
        return results
