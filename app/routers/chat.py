"""Day 6: FastAPI + LangChain 整合 —— POST /chat 接入真实 LLM"""
import logging
from fastapi import APIRouter
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from ..schemas.chat import ChatRequest, ChatResponse

# ---- 日志 ----
logger = logging.getLogger(__name__)

# ---- 路由 ----
router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


# ---- 工具定义 ----
def get_weather(city: str) -> str:
    """查询指定城市的天气"""
    return f"{city} 当前天气晴朗，气温 25°C"


# ---- Agent（模块级，所有请求共享一个实例）----
agent = create_agent(
    model=init_chat_model(
        "claude-sonnet-4-6",
        temperature=0.7,
        timeout=30,
        max_tokens=1000,
    ),
    tools=[get_weather],
    system_prompt="你是一个有帮助的AI助手。回答用户问题时简洁明了。",
)


# ---- 端点 ----
@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """接收用户消息，交给 LangChain Agent 处理并返回回复"""
    logger.info("收到消息: %s...", request.message[:80])

    try:
        result = agent.invoke({
            "messages": [{"role": "user", "content": request.message}]
        })
        last_msg = result["messages"][-1]
        # DeepSeek 返回的 content 可能是列表 [{type, text}, ...]，取 text 块拼成字符串
        if isinstance(last_msg.content, list):
            reply_text = "".join(
                b["text"] for b in last_msg.content if b.get("type") == "text"
            )
        else:
            reply_text = last_msg.content

        logger.info("回复成功，长度: %d", len(reply_text))
        return ChatResponse(
            reply=reply_text,
            model=request.model,
        )

    except Exception:
        logger.exception("Agent 调用失败")
        return ChatResponse(
            reply="抱歉，服务暂时不可用，请稍后重试。",
            model=request.model,
        )
