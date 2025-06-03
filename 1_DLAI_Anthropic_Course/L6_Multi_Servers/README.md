# L6 Multi-Server MCP System

## Introduction

This project demonstrates an advanced Model Context Protocol (MCP) implementation where a single chatbot client connects to **multiple MCP servers** simultaneously. This architecture allows the AI assistant to access a diverse set of tools from different specialized servers, enabling complex workflows that combine research, file operations, and web content fetching.

## System Overview

### What This System Does

The L6 Multi-Server MCP system extends the single-server approach from L5 to support multiple specialized servers:

- **Research Server**: Custom Python server for arXiv paper search and extraction
- **Filesystem Server**: Official MCP server for file and directory operations  
- **Fetch Server**: Official MCP server for web content retrieval

### Key Features

- **Tool Orchestration**: Single chatbot coordinates tools from multiple servers
- **Dynamic Server Configuration**: Servers defined in `server_config.json`
- **Efficient Async Communication**: Non-blocking I/O for multiple server connections
- **Resource Management**: Proper cleanup of all server connections

## Architecture: Processes, Threads, and Async

### Understanding the Concepts

#### **Processes** (What the MCP Servers Are)
##### Your Machine (Single Node)
├── Process 1: MCP Chatbot (Python)
├── Process 2: Research Server (Python)
├── Process 3: Filesystem Server (Node.js)
└── Process 4: Fetch Server (Python/uvx)



- **Separate programs** running independently
- **Separate memory spaces** for isolation
- **Different languages** (Python, Node.js) can coexist
- **Communication via stdin/stdout** (not network)

#### **Async** (How the Chatbot Manages Multiple Servers)
```python
# Single thread, single process, but handles multiple I/O operations
async def connect_to_servers(self):
    for server_name, server_config in servers.items():
        await self.connect_to_server(server_name, server_config)
```

**Why Async is Perfect Here:**
- **Efficient I/O handling**: While waiting for one server response, can process other tasks
- **Non-blocking operations**: No freezing while servers process requests
- **Single-threaded simplicity**: No complex thread synchronization needed

#### **Threads** (Not Used Here)

### Alternative approach (not implemented)
Single Process
├── Thread 1: Handle Research Server
├── Thread 2: Handle Filesystem Server
└── Thread 3: Handle Fetch Server



**Why We Use Async Instead of Threads:**
- ✅ **Simpler**: No shared memory or synchronization issues
- ✅ **Efficient**: Perfect for I/O-bound operations (waiting for server responses)
- ✅ **Python-friendly**: Avoids Global Interpreter Lock (GIL) limitations

### Real-World Analogy

Think of the system like a **restaurant manager** coordinating with specialized staff:

- **Restaurant Manager** = Your MCP Chatbot (async, single person)
- **Kitchen Staff** = Research Server (separate process/person)
- **Bartender** = Filesystem Server (separate process/person)  
- **Host** = Fetch Server (separate process/person)

The manager can efficiently handle multiple requests by delegating to specialists and managing the overall workflow without getting blocked waiting for any single task.

## Key Components

### 1. Server Configuration (`server_config.json`)
Defines all servers and their startup commands:
```json
{
    "mcpServers": {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
        },
        "research": {
            "command": "uv", 
            "args": ["run", "research_server.py"]
        },
        "fetch": {
            "command": "uvx",
            "args": ["mcp-server-fetch"]
        }
    }
}
```

### 2. Multi-Server Client (`mcp_chatbot.py`)
- **Multiple Sessions**: One `ClientSession` per server
- **Tool Mapping**: `tool_to_session` routes tool calls to correct server
- **Resource Management**: `AsyncExitStack` handles cleanup
- **Async Coordination**: Efficiently manages multiple server communications

### 3. Research Server (`research_server.py`)
Custom FastMCP server providing:
- `search_papers`: Search arXiv for academic papers
- `extract_info`: Retrieve stored paper information

## Benefits of This Architecture

1. **Modularity**: Each server has a specific purpose and can be developed independently
2. **Scalability**: Easy to add new servers by updating configuration
3. **Language Flexibility**: Servers can be written in different programming languages
4. **Tool Diversity**: Access to specialized tools from different domains
5. **Efficiency**: Async handling prevents blocking on slow server operations

## Usage Examples

### Complex Multi-Server Workflows
1. Fetch web content → Save to file → Search related papers → Write summary
2. List directory → Read files → Extract info → Generate report
3. Research topic → Fetch references → Organize findings → Create documentation


### Sample Queries
- `"Fetch https://example.com and save as 'content.md', then search for related papers"`
- `"List files in current directory, read the most recent one, and summarize it"`
- `"Search for 3 papers on neural networks and create a bibliography file"`

This multi-server approach transforms the chatbot from a simple tool user into a sophisticated **workflow orchestrator** capable of complex, multi-step operations across different domains.

## Getting Started

1. **Install dependencies**: `uv add mcp arxiv anthropic python-dotenv nest_asyncio`
2. **Set up environment**: Add your `ANTHROPIC_API_KEY` to `.env`
3. **Run the chatbot**: `uv run mcp_chatbot.py`
4. **Try multi-server queries**: Test workflows that combine tools from different servers

The system will automatically download and set up the official MCP servers (filesystem and fetch) on first run.