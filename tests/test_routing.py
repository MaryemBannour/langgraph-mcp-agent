"""Unit tests for the pure helper functions (no graph, no LLM)."""
from langchain_core.messages import AIMessage
from langgraph.graph import END

from agent import route_after_agent, tool_text
from tests.fakes import tool_call


def state_with(message):
    return {"messages": [message]}


def test_final_answer_goes_to_end():
    assert route_after_agent(state_with(AIMessage(content="Bonjour"))) == END


def test_read_tool_runs_without_approval():
    assert route_after_agent(state_with(tool_call("get_skills", {}))) == "tools"


def test_write_tool_requires_approval():
    assert route_after_agent(state_with(tool_call("add_project", {}))) == "approval"


def test_mixed_read_and_write_requires_approval():
    message = AIMessage(content="", tool_calls=[
        {"name": "get_skills", "args": {}, "id": "1"},
        {"name": "update_project", "args": {"id": "x"}, "id": "2"},
    ])
    assert route_after_agent(state_with(message)) == "approval"


def test_tool_text_handles_string_and_mcp_blocks():
    assert tool_text("hello") == "hello"
    assert tool_text([{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]) == "ab"