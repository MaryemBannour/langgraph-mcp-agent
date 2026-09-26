"""Command-line entry point: chat with the agent and approve write actions."""
import asyncio
import uuid

from langchain_core.exceptions import ModelError
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from agent import build_graph, create_llm, load_mcp_tools


async def main():
    tools = await load_mcp_tools()
    agent = build_graph(create_llm(), tools)
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}  # one thread = one conversation
    print("Agent prêt. Pose une question (ou 'q' pour quitter).\n")

    while True:
        question = input("Toi : ")
        if question.strip().lower() == "q":
            break

        try:
            result = await agent.ainvoke(
                {"messages": [HumanMessage(question)], "verifications": []}, config
            )

            # While the graph is paused, ask the user for approval
            while "__interrupt__" in result:
                for action in result["__interrupt__"][0].value["actions"]:
                    print(f"   ⚠️  L'agent veut exécuter {action['outil']} avec : {action['arguments']}")
                decision = input("   Tu confirmes ? (oui/non) : ").strip().lower()
                result = await agent.ainvoke(Command(resume=decision), config)

        except ModelError as error:
            # Any LLM error (quota 429, overload 503, unknown model 404...) must not crash the program
            print(f"   ❌ Erreur du modèle : {str(error)[:200]}\n")
            config = {"configurable": {"thread_id": str(uuid.uuid4())}}  # start a clean conversation
            continue

        for note in result.get("verifications", []):
            print(f"   [vérif] {note}")
        print(f"Agent : {result['messages'][-1].text}\n")


if __name__ == "__main__":
    asyncio.run(main())