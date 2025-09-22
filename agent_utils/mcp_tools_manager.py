import requests


class MCPToolsManager:
    """Manage MCP server tools integration"""

    def __init__(self, endpoint_url):
        self.endpoint_url = endpoint_url
        self.available_tools = {}
        self._initialize_tools()

    def _initialize_tools(self):
        """Initialize available tools from MCP server"""
        try:
            # Connect to MCP server and get available tools
            response = requests.get(f"{self.endpoint_url}/tools", timeout=5)
            if response.status_code == 200:
                self.available_tools = response.json()
        except Exception as e:
            print(f"Warning: Could not connect to MCP server: {e}")
            # Fallback to mock tools for development
            self.available_tools = {
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

    def call_tool(self, tool_name, parameters):
        """Call a specific MCP tool"""
        try:
            response = requests.post(
                f"{self.endpoint_url}/call_tool",
                json={
                    'tool': tool_name,
                    'parameters': parameters
                },
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Tool call failed: {response.status_code}"}
        except Exception as e:
            # Mock response for development
            return {
                "success": True,
                "result": f"Mock result for {tool_name} with parameters {parameters}",
                "tool": tool_name
            }

    def get_tools_list(self):
        """Get formatted list of tools for API response"""
        tools_list = []
        for tool_id, tool_data in self.available_tools.items():
            tools_list.append({
                'id': tool_id,
                'name': tool_data.get('name', tool_id),
                'description': tool_data.get('description', 'No description available'),
                'parameters': tool_data.get('parameters', [])
            })
        return tools_list

    def get_tools_count(self):
        """Get total count of available tools"""
        return len(self.available_tools)
