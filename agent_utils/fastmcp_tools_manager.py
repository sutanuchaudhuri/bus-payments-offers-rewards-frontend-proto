import asyncio
from fastmcp import Client
import requests


class FastMCPToolsManager:
    """FastMCP-based tools manager for better MCP server integration"""

    def __init__(self, endpoint_url):
        self.endpoint_url = endpoint_url
        self.available_tools = {}
        self.tools_list = []
        self._initialize_tools()

    def _initialize_tools(self):
        """Initialize available tools from MCP server using FastMCP"""
        try:
            # Use asyncio to run the async initialization
            asyncio.run(self._fetch_tools_async())
        except Exception as e:
            print(f"Warning: Could not connect to FastMCP server: {e}")
            # Fallback to mock tools for development
            self._setup_fallback_tools()

    async def _fetch_tools_async(self):
        """Fetch tools asynchronously using FastMCP client"""
        print("🔍 Testing FastMCP Client connection...")

        async with Client(self.endpoint_url) as client:
            print("✅ Successfully connected to FastMCP server")

            # Get tools list
            print("📋 Attempting to list tools...")
            tools = await client.list_tools()
            print(f"✅ Found {len(tools)} tools")

            # Process tools into our format
            self.available_tools = {}
            self.tools_list = []

            for i, tool in enumerate(tools):
                tool_id = tool.name
                tool_data = {
                    'name': tool.name,
                    'description': tool.description,
                    'parameters': getattr(tool, 'parameters', []) or []
                }

                self.available_tools[tool_id] = tool_data
                self.tools_list.append({
                    'id': tool_id,
                    'name': tool.name,
                    'description': tool.description,
                    'parameters': tool_data['parameters']
                })

                print(f"  {i+1}. {tool.name} - {tool.description}")

    def _setup_fallback_tools(self):
        """Setup fallback mock tools when FastMCP connection fails"""
        self.available_tools = {
            'health_check': {
                'name': 'Health Check',
                'description': 'Perform a comprehensive health check of the credit card payment system API',
                'parameters': []
            },
            'list_customers': {
                'name': 'List Customers',
                'description': 'Retrieve a paginated list of all customers in the system with optional email filtering',
                'parameters': ['page', 'limit', 'email_filter']
            },
            'create_customer': {
                'name': 'Create Customer',
                'description': 'Register a new customer account with personal information including name, email, phone, date of birth, and address',
                'parameters': ['name', 'email', 'phone', 'date_of_birth', 'address']
            },
            'get_customer_details': {
                'name': 'Get Customer Details',
                'description': 'Retrieve detailed information about a specific customer including full profile, contact information, registration date, and account status',
                'parameters': ['customer_id']
            },
            'payment_processor': {
                'name': 'Process Payment',
                'description': 'Process bus payment transactions',
                'parameters': ['amount', 'card_id', 'route_id']
            },
            'balance_checker': {
                'name': 'Check Balance',
                'description': 'Check customer account balance',
                'parameters': ['customer_id']
            },
            'schedule_lookup': {
                'name': 'Bus Schedule Lookup',
                'description': 'Look up bus schedules and routes',
                'parameters': ['route_id', 'stop_id', 'time']
            },
            'offer_manager': {
                'name': 'Manage Offers',
                'description': 'Get and apply customer offers',
                'parameters': ['customer_id', 'offer_type']
            }
        }

        self.tools_list = self.get_tools_list()

    def get_tools_list(self):
        """Get formatted list of tools for API response"""
        if not self.tools_list:
            # Generate tools list from available_tools if not already set
            tools_list = []
            for tool_id, tool_data in self.available_tools.items():
                tools_list.append({
                    'id': tool_id,
                    'name': tool_data.get('name', tool_id),
                    'description': tool_data.get('description', 'No description available'),
                    'parameters': tool_data.get('parameters', [])
                })
            return tools_list
        return self.tools_list

    def get_tools_count(self):
        """Get total count of available tools"""
        return len(self.available_tools)

    async def call_tool_async(self, tool_name, parameters):
        """Call a tool asynchronously using FastMCP"""
        try:
            async with Client(self.endpoint_url) as client:
                result = await client.call_tool(tool_name, parameters)
                return {
                    "success": True,
                    "result": result.content if hasattr(result, 'content') else str(result),
                    "tool": tool_name
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name
            }

    def call_tool(self, tool_name, parameters):
        """Synchronous wrapper for tool calling"""
        try:
            return asyncio.run(self.call_tool_async(tool_name, parameters))
        except Exception as e:
            # Fallback to mock response for development
            return {
                "success": True,
                "result": f"Mock result for {tool_name} with parameters {parameters}",
                "tool": tool_name
            }

    async def test_health_check(self):
        """Test health check tool specifically"""
        try:
            async with Client(self.endpoint_url) as client:
                print("🏥 Testing health check...")
                result = await client.call_tool("health_check")
                print(f"✅ Health check response: {result.content}")
                return result
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return None

    def refresh_tools(self):
        """Refresh tools list from MCP server"""
        self._initialize_tools()
        return self.get_tools_list()
