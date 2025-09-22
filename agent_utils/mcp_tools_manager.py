import requests
import asyncio
from fastmcp import Client
import sys


class MCPToolsManager:
    """Manage MCP server tools integration"""

    def __init__(self, endpoint_url):
        self.endpoint_url = endpoint_url
        self.available_tools = []
        self._initialize_tools()

    def _initialize_tools(self):
        """Initialize available tools from MCP server"""
        self.available_tools = self.get_tools() or []

    def get_tools(self):
        """Get tools from FastMCP server using async pattern"""
        try:
            # Use asyncio.run to execute the async function
            return asyncio.run(self._get_tools_async())
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def _get_tools_async(self):
        """Async method to get tools from FastMCP server"""
        print("🔍 Testing FastMCP Client connection...")

        # Use the same pattern as your working fastmcp_test.py
        async with Client(self.endpoint_url) as client:
            print("✅ Successfully connected to FastMCP server")

            # Test basic functionality
            print("📋 Attempting to list tools...")
            tools = await client.list_tools()
            print(f"✅ Found {len(tools)} tools")

            # Process tools into our format
            formatted_tools = []
            for i, tool in enumerate(tools):
                formatted_tool = {
                    'id': tool.name,
                    'name': tool.name,
                    'description': tool.description,
                    'parameters': getattr(tool, 'parameters', []) or []
                }
                formatted_tools.append(formatted_tool)
                print(f"  {i+1}. {tool.name} - {tool.description}")

            return formatted_tools

    def call_tool(self, tool_name, parameters):
        """Call a specific MCP tool using async pattern"""
        try:
            return asyncio.run(self._call_tool_async(tool_name, parameters))
        except Exception as e:
            print(f"❌ Tool call error: {e}")
            # Return error response instead of mock
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name
            }

    async def _call_tool_async(self, tool_name, parameters):
        """Async method to call MCP tools"""
        async with Client(self.endpoint_url) as client:
            result = await client.call_tool(tool_name, parameters)
            return {
                "success": True,
                "result": result.content if hasattr(result, 'content') else str(result),
                "tool": tool_name
            }

    def get_tools_list(self):
        """Get formatted list of tools for API response"""
        return self.available_tools

    def get_tools_count(self):
        """Get total count of available tools"""
        return len(self.available_tools)

    def refresh_tools(self):
        """Refresh tools list from MCP server"""
        self._initialize_tools()
        return self.get_tools_list()


if __name__ == "__main__":
    mcp_manager = MCPToolsManager("http://127.0.0.1:8000/sse")
    tools = mcp_manager.get_tools()
    print(f"Available tools: {len(tools) if tools else 0}")
    if tools:
        for tool in tools[:3]:  # Show first 3 tools
            print(f"  - {tool['name']}: {tool['description']}")
