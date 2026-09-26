import asyncio
from pathlib import Path
from langchain_mcp_adapters.client import MultiServerMCPClient

# Chemin vers ton serveur MCP (dossier voisin)
MCP_SERVER_PATH = Path(__file__).parent.parent / "-portfolio-mcp-server" / "src" / "server.js"


async def main():
    # 1. Le client MCP lance ton serveur Node en local (stdio)
    client = MultiServerMCPClient({
        "portfolio": {
            "command": "node",
            "args": [str(MCP_SERVER_PATH)],
            "transport": "stdio",
        }
    })

    # 2. On récupère les outils exposés par le serveur
    tools = await client.get_tools()
    print(f"{len(tools)} outils trouvés :\n")
    for tool in tools:
        print(f"- {tool.name} : {tool.description[:70]}...")

    # 3. On appelle un outil de lecture pour tester
    search = next(t for t in tools if t.name == "search_by_skill")
    result = await search.ainvoke({"keyword": "RAG"})
    print("\nRésultat de search_by_skill('RAG') :")
    print(str(result)[:500])


asyncio.run(main())