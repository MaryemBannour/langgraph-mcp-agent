import asyncio
from pathlib import Path
from langchain_mcp_adapters.client import MultiServerMCPClient

# path to the MCP server, sitting in the folder next door
MCP_SERVER_PATH = Path(__file__).parent.parent / "-portfolio-mcp-server" / "src" / "server.js"


async def main():
    # 1. the client starts the node server locally and talks to it over stdio
    client = MultiServerMCPClient({
        "portfolio": {
            "command": "node",
            "args": [str(MCP_SERVER_PATH)],
            "transport": "stdio",
        }
    })

    # 2. grab whatever tools the server exposes
    tools = await client.get_tools()
    print(f"{len(tools)} outils trouvés :\n")
    for tool in tools:
        print(f"- {tool.name} : {tool.description[:70]}...")

    # 3. call one read tool just to check it actually works
    search = next(t for t in tools if t.name == "search_by_skill")
    result = await search.ainvoke({"keyword": "RAG"})
    print("\nRésultat de search_by_skill('RAG') :")
    print(str(result)[:500])


asyncio.run(main())