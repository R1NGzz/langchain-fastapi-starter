
from langchain.agents import create_agent
from langchain_core.utils.uuid import uuid7
from langgraph.checkpoint.memory import InMemorySaver
# 子智能体：天气代理
def get_weather(city: str) -> str:
    """查询当前城市天气"""
    return f"{city} 天气晴朗"

# 创建带记忆智能体
agent = create_agent(
    model="claude-sonnet-4-6",
    tools=[get_weather],
    checkpointer=InMemorySaver()
)
# 会话唯一ID，维持上下文
config = {"configurable": {"thread_id": str(uuid7())}}

# 开启V3事件流
stream = agent.stream_events(
    {"messages": [{"role":"user","content":"旧金山天气"}]},
    config=config,
    version="v3"
)

# 同时监听对话文本 + 工具调用
for kind, item in stream.interleave("messages", "tool_calls"):
    if kind == "messages":
        # 逐字打印回答
        for token in item.text:
            print(token, end="", flush=True)
    elif kind == "tool_calls":
        print(f"\n调用工具：{item.tool_name} 参数：{item.input}")
        # 打印工具执行返回流式内容
        for delta in item.output_deltas:
            print(delta, end="")
        print(f"\n工具最终结果：{item.output}")

# 获取最终完整会话状态
final_state = stream.output