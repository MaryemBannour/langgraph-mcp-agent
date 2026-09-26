"""Integration test with the real MCP server (read-only). Skipped if Node or the server is missing."""
import asyncio
import shutil

import pytest

from agent import MCP_SERVER_PATH, load_mcp_tools

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None or not MCP_SERVER_PATH.exists(),
    reason="Node.js or the MCP server is not available",
)


def test_mcp_server_exposes_the_six_tools():
    tools = asyncio.run(load_mcp_tools())
    assert {t.name for t in tools} == {
        "get_experiences", "list_projects", "get_skills",
        "search_by_skill", "add_project", "update_project",
    }