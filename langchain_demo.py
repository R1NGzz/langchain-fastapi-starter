from langchain.agents import create_agent
import os
def get_weather(city:str) -> str:
    '''Get weather for a given city'''
    return f"it's always sunny in {city}"
api_key = os.getenv("ANTHROPIC_API_KEY")
agent = create_agent(
    model="claude-sonnet-4-6",
    tools=[get_weather],
    system_prompt="you are a helpful assistant",
)

result= agent.invoke(
    {"messages": [{"role":"user","content":"what's the weather in beijing?"}]}
)

print(result["messages"][-1].content_blocks)