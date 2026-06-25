from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
import os

# 自定义工具
def get_user_info() -> str:
    """查询用户个户个人信息"""
    return "暂无用户资料"

# 初始化智能体 + 内存记忆
agent = create_agent(
    model="claude-sonnet-4-6",
    tools=[get_user_info],
    checkpointer=InMemorySaver()  # 开启短时记忆
)

# 定义会话线程ID，不同ID隔离不同对话
thread_config = {"configurable": {"thread_id": "chat_001"}}

# 第一轮对话
res1 = agent.invoke(
    {"messages": [{"role":"user","content":"你好，我叫鲍勃"}]},
    thread_config
)
print(res1["messages"][-1].content)

# 第二轮自动记住名字
res2 = agent.invoke(
    {"messages": [{"role":"user","content":"我叫什么名字"}]},
    thread_config
)
print(res2["messages"][-1].content)