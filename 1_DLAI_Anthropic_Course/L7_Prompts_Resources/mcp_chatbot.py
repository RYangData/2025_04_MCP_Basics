from dotenv import load_dotenv
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from typing import List, Dict, TypedDict
from contextlib import AsyncExitStack
from pydantic import AnyUrl
import json
import asyncio
import re

load_dotenv()

class ToolDefinition(TypedDict):
    name: str
    description: str
    input_schema: dict

class MCP_ChatBot:

    def __init__(self):
        # Initialize session and client objects
        self.sessions: List[ClientSession] = []
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()
        self.available_tools: List[ToolDefinition] = []
        self.tool_to_session: Dict[str, ClientSession] = {}
        # NEW: For prompts and resources
        self.available_prompts: Dict[str, dict] = {}
        self.available_resources: Dict[str, ClientSession] = {}

    async def connect_to_server(self, server_name: str, server_config: dict) -> None:
        """Connect to a single MCP server."""
        try:
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()
            self.sessions.append(session)
            
            # List available tools for this session
            response = await session.list_tools()
            tools = response.tools
            print(f"\nConnected to {server_name} with tools:", [t.name for t in tools])
            
            for tool in tools:
                self.tool_to_session[tool.name] = session
                self.available_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })

            # NEW: List available resources
            try:
                resources_response = await session.list_resources()
                resources = resources_response.resources
                if resources:
                    print(f"  Resources:", [r.uri for r in resources])
                    for resource in resources:
                        self.available_resources[str(resource.uri)] = session
            except Exception as e:
                print(f"  No resources available from {server_name}")

            # NEW: List available prompts
            try:
                prompts_response = await session.list_prompts()
                prompts = prompts_response.prompts
                if prompts:
                    print(f"  Prompts:", [p.name for p in prompts])
                    for prompt in prompts:
                        self.available_prompts[prompt.name] = {
                            "description": prompt.description,
                            "arguments": prompt.arguments,
                            "session": session
                        }
            except Exception as e:
                print(f"  No prompts available from {server_name}")

        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")

    async def connect_to_servers(self):
        """Connect to all configured MCP servers."""
        try:
            with open("server_config.json", "r") as file:
                data = json.load(file)
            
            servers = data.get("mcpServers", {})
            
            for server_name, server_config in servers.items():
                await self.connect_to_server(server_name, server_config)
        except Exception as e:
            print(f"Error loading server configuration: {e}")
            raise

    # NEW: Handle resource requests
    async def get_resource(self, uri: str) -> str:
        """Get a resource from the appropriate server."""
        print(f"DEBUG: Trying to get resource: {uri}")
        print(f"DEBUG: Available resources: {list(self.available_resources.keys())}")
        
        # For dynamic resources, we need to find a session that can handle this type
        for resource_uri, session in self.available_resources.items():
            try:
                # Try the exact match first
                if resource_uri == uri:
                    url_obj = AnyUrl(uri)
                    response = await session.read_resource(url_obj)
                    
                    if response.contents:
                        content = response.contents[0]
                        if hasattr(content, 'text'):
                            return content.text
                        elif hasattr(content, 'blob'):
                            return f"Binary content found (blob of {len(content.blob)} bytes)"
                        else:
                            return str(content)
                    return "No content found"
                
                # For dynamic resources like papers://{topic}, try with any session from research server
                if (uri.startswith("papers://") and 
                    (resource_uri == "papers://folders" or "papers://" in resource_uri)):
                    
                    url_obj = AnyUrl(uri)
                    response = await session.read_resource(url_obj)
                    
                    if response.contents:
                        content = response.contents[0]
                        if hasattr(content, 'text'):
                            return content.text
                        elif hasattr(content, 'blob'):
                            return f"Binary content found (blob of {len(content.blob)} bytes)"
                        else:
                            return str(content)
                    return "No content found"
                    
            except Exception as e:
                print(f"DEBUG: Error trying resource {resource_uri} for {uri}: {e}")
                continue
        
        return f"Resource {uri} not found. Available resources: {list(self.available_resources.keys())}"

    # NEW: List available prompts
    async def list_prompts(self) -> str:
        """List all available prompts."""
        if not self.available_prompts:
            return "No prompts available."
        
        result = "Available prompts:\n\n"
        for name, info in self.available_prompts.items():
            result += f"- **{name}**: {info['description']}\n"
            if info['arguments']:
                # Fix: Access PromptArgument attributes, not dictionary keys
                args = [f"{arg.name}={getattr(arg, 'description', 'value')}" for arg in info['arguments']]
                result += f"  Usage: /prompt {name} {' '.join(args)}\n"
            result += "\n"
        return result

    # NEW: Execute a prompt
    async def execute_prompt(self, prompt_name: str, arguments: dict) -> str:
        """Execute a prompt with given arguments."""
        if prompt_name not in self.available_prompts:
            return f"Prompt '{prompt_name}' not found."
        
        prompt_info = self.available_prompts[prompt_name]
        session = prompt_info["session"]
        
        try:
            response = await session.get_prompt(prompt_name, arguments)
            
            # Safe handling of response components
            description = getattr(response, 'description', '') or ''
            
            # Safe handling of messages
            if response.messages and len(response.messages) > 0:
                message = response.messages[0]
                if hasattr(message, 'content') and hasattr(message.content, 'text'):
                    content_text = message.content.text or ''
                else:
                    content_text = str(message.content) if hasattr(message, 'content') else ''
            else:
                content_text = ''
            
            # Build result safely
            if description and content_text:
                return f"{description}\n\n{content_text}"
            elif description:
                return description
            elif content_text:
                return content_text
            else:
                return f"Prompt executed but returned no content."
                
        except Exception as e:
            return f"Error executing prompt {prompt_name}: {e}"

    async def process_query(self, query):
        messages = [{'role':'user', 'content':query}]
        response = self.anthropic.messages.create(max_tokens = 2024,
                                      model = 'claude-3-7-sonnet-20250219', 
                                      tools = self.available_tools,
                                      messages = messages)
        process_query = True
        while process_query:
            assistant_content = []
            for content in response.content:
                if content.type =='text':
                    print(content.text)
                    assistant_content.append(content)
                    if(len(response.content) == 1):
                        process_query= False
                elif content.type == 'tool_use':
                    assistant_content.append(content)
                    messages.append({'role':'assistant', 'content':assistant_content})
                    tool_id = content.id
                    tool_args = content.input
                    tool_name = content.name
                    
                    print(f"Calling tool {tool_name} with args {tool_args}")
                    
                    # Call a tool using the correct session
                    session = self.tool_to_session[tool_name]
                    result = await session.call_tool(tool_name, arguments=tool_args)
                    messages.append({"role": "user", 
                                      "content": [
                                          {
                                              "type": "tool_result",
                                              "tool_use_id":tool_id,
                                              "content": result.content
                                          }
                                      ]
                                    })
                    response = self.anthropic.messages.create(max_tokens = 2024,
                                      model = 'claude-3-7-sonnet-20250219', 
                                      tools = self.available_tools,
                                      messages = messages) 
                    
                    if(len(response.content) == 1 and response.content[0].type == "text"):
                        print(response.content[0].text)
                        process_query= False

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Chatbot Started!")
        print("Type your queries or 'quit' to exit.")
        print("Special commands:")
        print("  @folders - List available topics")
        print("  @<topic> - Get papers for a topic")
        print("  /prompts - List available prompts")
        print("  /prompt <name> <args> - Execute a prompt")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
        
                if query.lower() == 'quit':
                    break

                # NEW: Handle resource requests
                if query.startswith('@'):
                    resource_name = query[1:]
                    if resource_name == 'folders':
                        uri = "papers://folders"
                    else:
                        uri = f"papers://{resource_name}"
                    
                    result = await self.get_resource(uri)
                    print(result)
                    continue

                # NEW: Handle prompt commands
                if query.startswith('/'):
                    if query == '/prompts':
                        result = await self.list_prompts()
                        print(result)
                        continue
                    elif query.startswith('/prompt '):
                        # Parse prompt command: /prompt name arg1=value1 arg2=value2
                        parts = query[8:].split(' ', 1)
                        prompt_name = parts[0]
                        
                        arguments = {}
                        if len(parts) > 1:
                            # Parse arguments
                            arg_string = parts[1]
                            for arg_pair in arg_string.split():
                                if '=' in arg_pair:
                                    key, value = arg_pair.split('=', 1)
                                    # Keep all values as strings for prompt templates
                                    arguments[key] = value
                        
                        result = await self.execute_prompt(prompt_name, arguments)
                        # Pass the prompt result to the LLM
                        await self.process_query(result)
                        continue
                
                # Regular query processing
                await self.process_query(query)
                print("\n")
                    
            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Cleanly close all resources using AsyncExitStack."""
        await self.exit_stack.aclose()

async def main():
    chatbot = MCP_ChatBot()
    try:
        await chatbot.connect_to_servers()
        await chatbot.chat_loop()
    finally:
        await chatbot.cleanup()

if __name__ == "__main__":
    asyncio.run(main())