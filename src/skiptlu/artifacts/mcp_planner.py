from __future__ import annotations

from typing import Any

from skiptlu.tasks.specification import PracticalTaskSpecification


class McpOperationPlanner:
    """Plan non-destructive MCP enhancements for an already-rendered artifact.

    Native rendering remains responsible for creating document content.
    Therefore this planner never blindly re-adds headings, figures, or tables.
    MCP operations are opt-in through specification metadata.
    """

    def plan(self, specification: PracticalTaskSpecification) -> list[dict[str, Any]]:
        metadata = specification.metadata
        configured = metadata.get("mcp_operations", [])
        if configured is None:
            return []
        if not isinstance(configured, list):
            raise ValueError("metadata.mcp_operations must be a list")

        operations: list[dict[str, Any]] = []
        for item in configured:
            if not isinstance(item, dict):
                raise ValueError("Each MCP operation must be an object")
            tool = item.get("tool")
            if not isinstance(tool, str) or not tool:
                raise ValueError("Each MCP operation requires a non-empty tool")
            arguments = item.get("arguments", {})
            if not isinstance(arguments, dict):
                raise ValueError(f"MCP operation arguments for {tool} must be an object")
            operations.append(
                {
                    "tool": tool,
                    "arguments": dict(arguments),
                }
            )
        return operations
