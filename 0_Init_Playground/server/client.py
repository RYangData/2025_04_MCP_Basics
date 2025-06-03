import asyncio

from langchain_groq import ChatGroq

from mcp_use import MCPAgent, MCPClient
import os
from dotenv import load_dotenv
async def run_memory_chat():
    """Run a chat using MCPAgent's build-in conversation memory."""
    load_dotenv()
    os.environ["GROQ_API_KEY"] = "gsk_1234567890"
    api_key = os.getenv("GROQ_API_KEY")

    # config file path - change this to your config file
    config_file = "server/weather.json"
    
    print("initialising chat ...")
    
    # create MCP client and agent with memory enbled
    
    client = MCPClient.from_config_file(config_file)
    llm = ChatGroq(model = "qwen-qwq-32b")
    
    agent = MCPAgent(
        llm = llm, 
        client = client,
        max_steps = 15, 
        memory_enabled = True,
        verbose = True,
    )
    
    print("\n===== Interactive MCP Chat =====")
    print("Type 'exit' to quit")
    
    print("Type clear to clear conversation history")
    print("--------------------------------")
    
    try:
        # main chat loop 
        while True:
            # get user input
            user_input = input("You: ")
            
            # handle exit command
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting chat...")
                break
            
            # handle clear command
            if user_input.lower() == "clear":
                agent.clear_conversation()
                print("Conversation history cleared.")
                continue
            
            try:
                
                # process user input
                response = await agent.run(user_input)
                print(f"MCP: {response}")
            except Exception as e:
                print(f"Error: {e}")
                print("Please try again.")
                
    finally:
        # clean up 
        if client and client.sessions():
            await client.close_all_sessions()
            
if __name__ == "__main__":
    asyncio.run(run_memory_chat())