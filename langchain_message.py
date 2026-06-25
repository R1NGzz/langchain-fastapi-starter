from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

# 初始化对话模型
model = init_chat_model("claude-sonnet-4-6")

# 模型发起工具调用
ai_call_msg = AIMessage(
    content=[],
    tool_calls=[{
        "name": "get_weather",
        "args": {"location": "旧金山"},
        "id": "call_001"
    }]
)

# 组装工具执行结果消息
tool_result = "晴天，22摄氏度"
tool_msg = ToolMessage(
    content=tool_result,
    tool_call_id="call_001" # 必须和调用ID一致
)

# 送入会话继续推理
messages = [
    HumanMessage("旧金山天气如何"),
    ai_call_msg,
    tool_msg
]
response = model.invoke(messages)
print(response)