from mcp import ClientSession
from mcp.client.sse import sse_client
from contextlib import AsyncExitStack
import asyncio

async def test_remote_server():
    """Test connection to remote MCP server."""
    
    server_url = "http://127.0.0.1:8001/sse"
    
    async with AsyncExitStack() as stack:
        # Connect to remote server via SSE
        sse_transport = await stack.enter_async_context(
            sse_client(server_url)
        )
        
        read, write = sse_transport
        session = await stack.enter_async_context(
            ClientSession(read, write)
        )
        
        # Initialize connection
        await session.initialize()
        print(f"✅ Connected to remote server at {server_url}")
        
        # List tools
        tools_response = await session.list_tools()
        print(f"📚 Available tools: {[t.name for t in tools_response.tools]}")
        
        # List resources  
        try:
            resources_response = await session.list_resources()
            print(f"📂 Available resources: {[r.uri for r in resources_response.resources]}")
        except:
            print("📂 No resources available")
            
        # List prompts
        try:
            prompts_response = await session.list_prompts()
            print(f"💡 Available prompts: {[p.name for p in prompts_response.prompts]}")
        except:
            print("💡 No prompts available")
            
        # Test a tool
        print("\n🔍 Testing search_papers tool...")
        result = await session.call_tool("search_papers", {"topic": "quantum computing", "max_results": 2})
        print(f"Tool result: {result.content[:200]}...")

if __name__ == "__main__":
    asyncio.run(test_remote_server())