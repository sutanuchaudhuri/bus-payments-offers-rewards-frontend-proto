# Org Bus Payments & Rewards Chat Application

A Flask-based web application using OpenAI Agents with FastMCP integration for multi-agent customer support.

## Features

- 🤖 **Multi-Agent Orchestration** - Payment, Offers, Bus Schedule, and Support agents
- 💬 **Real-time Chat Interface** - Customer dropdown with session management
- 🗄️ **SQLite Session Persistence** - Chat history and context management
- 🔧 **MCP Tools Integration** - 76+ tools via FastMCP server
- 📊 **Visualization Dashboard** - Session stats and agent usage analytics
- 🎯 **Org Branding** - Professional UI with bank styling

## Quick Start

### 1. Environment Setup

Copy the environment template and configure your settings:

```bash
cp .env.sample .env
```

Edit `.env` file with your actual values:

```bash
# Required Configuration
MCP_ENDPOINT_SSE=http://127.0.0.1:8000/sse
OPENAI_API_KEY=your-actual-openai-api-key-here
SECRET_KEY=your-secure-secret-key-here
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
python main.py
```

The application will start on `http://localhost:5010`

## Application URLs

- **Main Chat Interface**: `http://localhost:5010/`
- **MCP Tools Dashboard**: `http://localhost:5010/mcp-tools`

## Project Structure

```
├── main.py                 # Flask application entry point
├── requirements.txt        # Python dependencies
├── .env.sample            # Environment variables template
├── templates/             # HTML templates
│   ├── index.html         # Main chat interface
│   └── mcp_tools.html     # MCP tools dashboard
├── agent_utils/           # Core utilities package
│   ├── mcp_tools_manager.py    # FastMCP integration
│   ├── session_manager.py      # Session management
│   ├── context_manager.py      # Context handling
│   ├── agents/                 # Agent orchestration
│   │   └── agent_orchestrator.py
│   └── database/              # Database layer
│       ├── database_manager.py
│       └── *_dao.py          # Data access objects
└── test/                  # Testing utilities
    └── fastmcp_test.py    # MCP connection testing
```

## Security Notice

⚠️ **Important**: Never commit your `.env` file to Git! It contains sensitive API keys.

- ✅ Use `.env.sample` for documentation
- ✅ Add real values to `.env` locally
- ✅ The `.gitignore` file excludes `.env` automatically

## MCP Server Integration

This application connects to a FastMCP server to access 76+ tools including:

- Customer management (CRUD operations)
- Payment processing
- Credit card management
- Offer and rewards management
- Travel booking services
- Shopping integration
- Analytics and reporting

## Development

To add new agents or tools:

1. **New Agents**: Add to `agent_utils/agents/agent_orchestrator.py`
2. **Database Changes**: Modify `agent_utils/database/database_manager.py`
3. **MCP Tools**: Configure your FastMCP server endpoint

## Troubleshooting

- **MCP Connection Issues**: Check that your FastMCP server is running on the specified endpoint
- **OpenAI Errors**: Verify your API key is valid and has sufficient credits
- **Database Issues**: Delete `chat_sessions.db` to reset the database
