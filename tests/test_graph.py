"""End-to-end tests of the agent graph with a scripted LLM and fake tools."""
import asyncio
import uuid

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command

from agent import build_graph
from tests.fakes import make_fake_tools, scripted_llm, tool_call

NEW_PROJECT = {"name": "Agent Test", "description": "d", "technologies": ["Python"], "date": "2026"}


def run(agent, question, answers=()):
    """Run one question; answer each approval pause with the next value in `answers`."""
    async def _run():
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        result = await agent.ainvoke(
            {"messages": [HumanMessage(question)], "verifications": []}, config
        )
        interrupts = 0
        for answer in answers:
            if "__interrupt__" not in result:
                break
            interrupts += 1
            result = await agent.ainvoke(Command(resume=answer), config)
        return result, interrupts
    return asyncio.run(_run())


def test_read_only_question_never_pauses():
    projects = []
    llm = scripted_llm(tool_call("get_skills", {}), AIMessage(content="RAG et MCP."))
    agent = build_graph(llm, make_fake_tools(projects))

    result, interrupts = run(agent, "Mes compétences ?", answers=["oui"])

    assert interrupts == 0
    assert result["messages"][-1].text == "RAG et MCP."


def test_approved_write_is_executed_and_verified():
    projects = []
    llm = scripted_llm(tool_call("add_project", NEW_PROJECT), AIMessage(content="Ajouté."))
    agent = build_graph(llm, make_fake_tools(projects))

    result, interrupts = run(agent, "Ajoute un projet", answers=["oui"])

    assert interrupts == 1
    assert [p["id"] for p in projects] == ["agent-test"]
    assert "vérifié" in result["verifications"][0]


def test_rejected_write_is_not_executed():
    projects = []
    llm = scripted_llm(tool_call("add_project", NEW_PROJECT), AIMessage(content="Annulé."))
    agent = build_graph(llm, make_fake_tools(projects))

    result, interrupts = run(agent, "Ajoute un projet", answers=["non"])

    assert interrupts == 1
    assert projects == []  # nothing was written
    assert "refusée" in result["messages"][-2].content  # the LLM was told it was refused


def test_failed_write_is_reported_by_verification():
    projects = [{"id": "agent-test", "name": "Agent Test", "technologies": [], "date": "2025"}]
    llm = scripted_llm(tool_call("add_project", NEW_PROJECT), AIMessage(content="Déjà existant."))
    agent = build_graph(llm, make_fake_tools(projects))

    result, _ = run(agent, "Ajoute un projet", answers=["oui"])

    assert len(projects) == 1  # no duplicate created
    assert "a échoué" in result["verifications"][0]