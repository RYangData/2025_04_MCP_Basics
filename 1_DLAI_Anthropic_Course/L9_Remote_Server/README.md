# L9 Remote MCP Server

## Overview

This project demonstrates how to create and deploy **remote MCP servers** using SSE (Server-Sent Events) transport. Unlike local servers that run as subprocesses, remote servers run independently and can be accessed over HTTP, making them deployable to cloud platforms.

## Key Architecture Differences

### Local vs Remote MCP Servers

| Feature | L7 (Local) | L9 (Remote) |
|---------|------------|-------------|
| **Transport** | `stdio` | `sse` |
| **Process Model** | Client launches server subprocess | Independent server process |
| **Connection** | stdin/stdout pipes | HTTP/SSE connections |
| **Scalability** | Single client | Multiple concurrent clients |
| **Deployment** | Local machine only | Cloud platforms |
| **Server Lifecycle** | Tied to client | Independent |

### Architecture Diagrams

**L7 Local Architecture:**
```
┌─────────────┐    stdio    ┌─────────────┐
│   Client    ├────────────►│   Server    │
│             │◄────────────┤ (subprocess)│
└─────────────┘             └─────────────┘
```

**L9 Remote Architecture:**
```
┌─────────────┐  HTTP/SSE   ┌─────────────┐
│   Client    ├────────────►│   Server    │
│             │◄────────────┤(independent)│
└─────────────┘             └─────────────┘
     │                           │
     │                           │
┌─────────────┐                 │
│  Client 2   ├─────────────────┘
│             │
└─────────────┘
```

## Server Implementation

### Key Changes from Local Server

1. **Port Specification:**
```python
# L7: No port needed
mcp = FastMCP("research")

# L9: Specify port for remote access
mcp = FastMCP("research", port=8001)
```

2. **Transport Change:**
```python
# L7: stdio transport
mcp.run(transport='stdio')

# L9: SSE transport  
mcp.run(transport='sse')
```

3. **Server URL:**
- **Server runs at:** `http://localhost:8001`
- **Client connects to:** `http://localhost:8001/sse`

## Available Features

### Tools
- **`search_papers(topic, max_results)`** - Search arXiv for academic papers
- **`extract_info(paper_id)`** - Get detailed paper information

### Resources
- **`papers://folders`** - List available research topics
- **`papers://{topic}`** - Get papers for specific topic

### Prompts
- **`generate_search_prompt(topic, num_papers)`** - Generate research prompts

## Usage Instructions

### 1. Start the Remote Server

```bash
# Navigate to project directory
cd L9_Remote_Server

# Activate virtual environment
source .venv/bin/activate

# Start server (keep terminal open)
uv run research_server.py
```

Server will display:
```
INFO:     Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C to quit)
```

### 2. Test with MCP Inspector

In a **new terminal**:
```bash
npx @modelcontextprotocol/inspector
```

Configure Inspector:
- **Transport Type:** `SSE`
- **URL:** `http://127.0.0.1:8001/sse`

### 3. Test with Remote Client

```bash
# In a new terminal
uv run remote_client.py
```

Expected output:
```
✅ Connected to remote server at http://127.0.0.1:8001/sse
📚 Available tools: ['search_papers', 'extract_info']
📂 Available resources: [AnyUrl('papers://folders')]
💡 Available prompts: ['generate_search_prompt']
🔍 Testing search_papers tool...
```

## Client Implementation

### Remote Client vs Local Client

**Local Client (L7):**
```python
from mcp.client.stdio import stdio_client

# Client launches server as subprocess
server_params = StdioServerParameters(
    command="uv", 
    args=["run", "research_server.py"]
)

async with stdio_client(server_params) as (read, write):
    # ...
```

**Remote Client (L9):**
```python
from mcp.client.sse import sse_client

# Client connects to running server
server_url = "http://127.0.0.1:8001/sse"

async with sse_client(server_url) as (read, write):
    # ...
```

## Deployment Options

### Local Development
- Run server locally on `localhost:8001`
- Test with local clients and MCP Inspector

### Cloud Deployment

#### Render.com (Free Tier)
1. Push code to GitHub repository
2. Connect GitHub to Render.com
3. Create new Web Service
4. Set build/start commands:
   ```
   Build: uv sync
   Start: uv run research_server.py
   ```

#### CloudFlare Workers
- Deploy using CloudFlare's MCP server guides
- Serverless deployment option

#### Traditional Cloud (AWS/GCP/Azure)
- Deploy as containerized application
- Use Docker with proper port exposure

### Environment Variables for Deployment
```bash
# For production deployment
export PORT=8001
export HOST=0.0.0.0
```

Update server code:
```python
import os
port = int(os.getenv("PORT", 8001))
host = os.getenv("HOST", "127.0.0.1")
mcp = FastMCP("research", port=port)
```

## Alternative Transports

### Streamable HTTP (Alternative to SSE)
```python
# Server
mcp.run(transport="streamable-http")

# Client  
from mcp.client.streamable_http import streamablehttp_client
async with streamablehttp_client("http://server/mcp/") as transport:
    # ...
```

**Options:**
- **Stateful:** `FastMCP("research")` - Maintains session state
- **Stateless:** `FastMCP("research", stateless_http=True)` - No session persistence

## Benefits of Remote Servers

### Scalability
- **Multiple clients** can connect simultaneously
- **Load balancing** possible with multiple server instances
- **Horizontal scaling** in cloud environments

### Deployment Flexibility  
- **Cloud platforms** support
- **Containerization** ready
- **Microservices** architecture compatible

### Development Benefits
- **Server-client separation** enables independent development
- **Testing isolation** - test server and client separately
- **Production readiness** - path to real-world deployment

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure server is running before connecting client
   - Check port is not blocked by firewall

2. **404 Errors on Root Path**
   - Normal behavior - server only responds to `/sse` endpoint
   - Use correct URL: `http://localhost:8001/sse`

3. **CORS Issues (in browser)**
   - Configure CORS headers for web client deployment
   - Use same-origin requests when possible

### Debug Commands
```bash
# Check if server is running
curl http://localhost:8001/sse

# Check server logs
# Monitor terminal where server is running

# Test client connection
uv run remote_client.py
```

## Next Steps

1. **Deploy to cloud platform** (Render.com, CloudFlare, etc.)
2. **Create web-based client** using browser SSE APIs
3. **Add authentication** for production deployment
4. **Implement load balancing** for high availability
5. **Add monitoring and logging** for production systems

## Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [CloudFlare MCP Deployment Guide](https://developers.cloudflare.com/agents/guides/remote-mcp-server/)
- [Render.com Deployment](https://render.com/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
