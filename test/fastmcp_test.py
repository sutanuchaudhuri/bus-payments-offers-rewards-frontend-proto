import asyncio
from fastmcp import Client
import sys
MCP_ENDPOINT_SSE="http://127.0.0.1:8000/sse"
async def simple_test():
    """Simple test to verify FastMCP connection"""
    try:
        print("🔍 Testing FastMCP Client connection...")

        # Try connecting to the server
        async with Client(MCP_ENDPOINT_SSE) as client:
            print("✅ Successfully connected to FastMCP server")

            # Test basic functionality
            print("📋 Attempting to list tools...")
            tools = await client.list_tools()
            print(f"✅ Found {len(tools)} tools")

            # List first few tools
            for i, tool in enumerate(tools[:]):
                print(f"  {i+1}. {tool.name} - {tool.description}")

            # Test a simple tool call
            print("🏥 Testing health check...")
            result = await client.call_tool("health_check")
            print(f"✅ Health check response: {result.content}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_test())