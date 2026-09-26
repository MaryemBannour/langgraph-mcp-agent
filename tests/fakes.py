"""Test doubles: a scripted fake LLM and in-memory fake tools (no API key, no MCP server)."""
import json

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import StructuredTool


class FakeLLM(GenericFakeChatModel):
    """Returns pre-written AI messages, one per call, and accepts bind_tools()."""

    def bind_tools(self, tools, **kwargs):
        return self


def scripted_llm(*responses: AIMessage) -> FakeLLM:
    return FakeLLM(messages=iter(responses))


def tool_call(name: str, args: dict, call_id: str = "call-1") -> AIMessage:
    """An AI message asking to call one tool."""
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": call_id}])


def make_fake_tools(projects: list[dict]):
    """Fake versions of the MCP tools, backed by a plain Python list."""

    def list_projects(technology: str = "") -> str:
        """List projects."""
        return json.dumps(projects)

    def get_skills() -> str:
        """Get skills."""
        return json.dumps({"ia": ["RAG", "MCP"]})

    def add_project(name: str, description: str, technologies: list[str], date: str) -> str:
        """Add a project."""
        project_id = name.lower().replace(" ", "-")
        if any(p["id"] == project_id for p in projects):
            return json.dumps({"error": f"Un projet avec l'id \"{project_id}\" existe déjà."})
        project = {"id": project_id, "name": name, "description": description,
                   "technologies": technologies, "date": date}
        projects.append(project)
        return json.dumps({"message": "Projet ajouté avec succès.", "project": project})

    def update_project(id: str, date: str = "") -> str:
        """Update a project."""
        for p in projects:
            if p["id"] == id:
                p["date"] = date or p["date"]
                return json.dumps({"message": "Projet mis à jour.", "project": p})
        return json.dumps({"error": f"Aucun projet trouvé avec l'id \"{id}\"."})

    return [StructuredTool.from_function(f) for f in
            (list_projects, get_skills, add_project, update_project)]