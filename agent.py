import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

load_dotenv()

MCP_SERVER_PATH = Path(__file__).parent.parent / "-portfolio-mcp-server" / "src" / "server.js"
READ_TOOLS = {"get_experiences", "list_projects", "get_skills", "search_by_skill"}

SYSTEM_PROMPT = (
    "Tu es un assistant qui répond aux questions sur le profil professionnel de Maryem Bannour. "
    "Utilise toujours les outils disponibles pour obtenir les informations, n'invente rien. "
    "Réponds en français, de façon courte et claire."
)


async def build_agent():
    # 1 connect to the MCP server and pull its tools
    client = MultiServerMCPClient({
        "portfolio": {
            "command": "node",
            "args": [str(MCP_SERVER_PATH)],
            "transport": "stdio",
        }
    })
    all_tools = await client.get_tools()
    tools = [t for t in all_tools if t.name in READ_TOOLS]  # day 2: read-only for now

    # 2 the LLM, with the tools handed over to it
    llm = ChatGoogleGenerativeAI(model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    llm_with_tools = llm.bind_tools(tools)

    # 3 "agent" node: the LLM reads the history and decides - answer, or call a tool
    async def agent_node(state: MessagesState):
        messages = [SystemMessage(SYSTEM_PROMPT)] + state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    # 4 wire up the graph
    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)  # tool requested? -> "tools", else -> END
    graph.add_edge("tools", "agent")                       # once the tool ran, back to the LLM

    return graph.compile()


async def main():
    agent = await build_agent()
    print("Agent prêt. Pose une question (ou 'q' pour quitter).\n")
    while True:
        question = input("Toi : ")
        if question.strip().lower() == "q":
            break
        result = await agent.ainvoke({"messages": [HumanMessage(question)]})

        # show which tools were used, then the final answer
        for msg in result["messages"]:
            for call in getattr(msg, "tool_calls", []) or []:
                print(f"   [outil] {call['name']}({call['args']})")
        print(f"Agent : {result['messages'][-1].text}\n")


if __name__ == "__main__":
    asyncio.run(main())