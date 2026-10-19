from __future__ import annotations

import json
import os
import shlex
from pathlib import Path

from skiptlu.artifacts.enhancer import ArtifactEnhancer, NoOpArtifactEnhancer, McpArtifactEnhancer
from skiptlu.artifacts.mcp_planner import McpOperationPlanner
from skiptlu.artifacts.word_mcp import McpWordAdapter, McpWordServerConfig


def build_word_enhancer_from_env(project_root: Path) -> ArtifactEnhancer:
    mode = os.getenv("SKIPTLU_WORD_ARTIFACT_MODE", "native").strip().lower()
    if mode in {"native", "off", "disabled"}:
        return NoOpArtifactEnhancer()

    if mode != "mcp":
        raise ValueError("SKIPTLU_WORD_ARTIFACT_MODE must be one of: native, mcp")

    command = os.getenv("SKIPTLU_WORD_MCP_COMMAND")
    if not command:
        raise ValueError("SKIPTLU_WORD_MCP_COMMAND is required in MCP mode")

    args_json = os.getenv("SKIPTLU_WORD_MCP_ARGS_JSON")
    if args_json:
        parsed_args = json.loads(args_json)
        if not isinstance(parsed_args, list) or not all(isinstance(item, str) for item in parsed_args):
            raise ValueError("SKIPTLU_WORD_MCP_ARGS_JSON must be a JSON string array")
        args = tuple(parsed_args)
    else:
        args = tuple(shlex.split(os.getenv("SKIPTLU_WORD_MCP_ARGS", "")))

    config = McpWordServerConfig(
        command=command,
        args=args,
        cwd=Path(os.getenv("SKIPTLU_WORD_MCP_CWD")) if os.getenv("SKIPTLU_WORD_MCP_CWD") else None,
        allowed_root=Path(os.getenv("SKIPTLU_WORD_MCP_ROOT", str(project_root / "artifacts"))),
    )
    adapter = McpWordAdapter(config)
    return McpArtifactEnhancer(adapter, planner=McpOperationPlanner())
