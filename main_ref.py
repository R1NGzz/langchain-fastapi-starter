"""
Day 1: FastAPI 骨架 + 第一个 LLM API 调用
===========================================
Agent 开发的核心：用 FastAPI 把 LLM 能力封装成 HTTP API 服务。

概念速览（面试常考）：
- FastAPI: Python 异步 Web 框架，Agent 系统的 API 层标配
- Pydantic: 数据校验，定义 API 的入参和出参结构
- uvicorn: ASGI 服务器，跑 FastAPI 的引擎
- Async I/O: 用 async/await 处理并发请求，不阻塞
"""

from fastapi import FastAPI
from pydantic import BaseModel, Field
from openai import AsyncOpenAI

# ============================================================
# 1. 创建 FastAPI 应用（整个 Agent 服务的入口）
# ============================================================
app = FastAPI(
    title="Agent Learn - Day 1",
    description="我的第一个 Agent API 服务",
    version="0.1.0",
)


# ============================================================
# 2. Pydantic 模型 —— 定义请求和响应的"形状"
# ============================================================
# 面试考点：Pydantic 自动校验入参，不合法的请求直接返回 422，
# 不用手写 if-else 校验，这是生产级 API 的基本要求。

class ChatRequest(BaseModel):
    """用户发来的聊天请求"""
    message: str = Field(..., min_length=1, description="用户输入的问题")
    system_prompt: str = Field(
        default="你是一个有帮助的AI助手。",
        description="系统提示词，定义AI的人设"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="生成随机性，0=确定，2=最随机"
    )


class ChatResponse(BaseModel):
    """返回给用户的聊天响应"""
    reply: str = Field(..., description="AI 的回复内容")
    model: str = Field(..., description="使用的模型名称")
    tokens_used: int = Field(default=0, description="消耗的 token 数")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str


# ============================================================
# 3. 路由 —— API 的 URL 端点
# ============================================================

# --- 3a. 最简单的 GET 端点 ---
# 访问 http://localhost:8000/ 就能看到
@app.get("/")
async def root():
    """根路径，等同于 API 的'首页'"""
    return {"message": "🚀 Agent Learn API 已启动！访问 /docs 查看交互式文档"}


# --- 3b. 健康检查端点 ---
# 面试考点：生产环境必须要有 health check，k8s/docker 用它来判断服务是否存活
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查 —— 部署和监控的基础"""
    return HealthResponse(status="healthy", version="0.1.0")


# --- 3c. 路径参数 ---
# /hello/小明 → "你好，小明！"
@app.get("/hello/{name}")
async def hello_name(name: str):
    """路径参数示例：name 从 URL 路径中提取"""
    return {"greeting": f"你好，{name}！欢迎来到 Agent 开发的世界 👋"}


# --- 3d. 查询参数 ---
# /search?q=agent框架&limit=5
@app.get("/search")
async def search(q: str = "", limit: int = 10):
    """查询参数示例：?q=xxx&limit=xxx"""
    return {
        "query": q,
        "limit": limit,
        "message": f"搜索 '{q}'，返回前 {limit} 条结果（还没接入搜索引擎）"
    }


# --- 3e. POST 端点 —— 核心：调用 LLM ---
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    核心端点：接收用户消息，调用 LLM，返回回复。

    这是 Agent 系统最基础的单元 —— 后面我们会在它的基础上：
    - 加 RAG（检索增强生成）
    - 加 Tool Calling（工具调用）
    - 加 Memory（多轮对话记忆）
    - 加 Multi-Agent（多智能体协作）
    """

    # ---- 检查 API key（必须在创建客户端之前）----
    # 面试考点：fail-fast 原则 —— 依赖缺失就提前返回友好信息
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return ChatResponse(
            reply="⚠️ 未设置 OPENAI_API_KEY 环境变量。\n\n"
                  "两种方式解决：\n"
                  "1. 设置环境变量：export OPENAI_API_KEY='sk-xxx'\n"
                  "2. 用本地模型（推荐）：安装 Ollama，用 /chat/local 端点\n\n"
                  "试试 GET /chat/mock 端点，不需要 API key 也能体验。",
            model="none",
            tokens_used=0,
        )

    # ---- 初始化 LLM 客户端 ----
    # 面试考点：
    # - 使用 OpenAI 兼容接口是行业标准，几乎所有 LLM 服务都兼容
    # - base_url 可以换成任何兼容的服务（vLLM、Ollama、DeepSeek 等）
    # - api_key 从环境变量读取是安全最佳实践
    client = AsyncOpenAI(
        base_url="https://api.openai.com/v1",  # 可以换成其他兼容的 API
        api_key=api_key,
    )

    # ---- 调用 LLM ----
    # 面试考点：三个核心参数
    # - model: 模型选择，gpt-4o-mini 便宜够用
    # - messages: 消息列表，system 定义人设，user 是用户问题
    # - temperature: 控制随机性
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.message},
            ],
            temperature=request.temperature,
        )

        reply_text = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else 0

        return ChatResponse(
            reply=reply_text,
            model=response.model,
            tokens_used=tokens,
        )

    except Exception as e:
        # 面试考点：错误处理 —— 不要把原始错误直接暴露给客户端
        return ChatResponse(
            reply=f"抱歉，LLM 调用失败：{str(e)[:200]}",
            model="error",
            tokens_used=0,
        )


# --- 3f. Mock 聊天端点（无需 API key，用于学习测试）---
@app.get("/chat/mock")
async def chat_mock(message: str = "什么是 Agent？"):
    """
    模拟聊天端点 —— 不调用真实 LLM，用于理解请求/响应流程。

    访问示例：
    http://localhost:8000/chat/mock?message=什么是RAG
    """
    return {
        "request": {
            "message": message,
        },
        "response": {
            "reply": f'这是模拟回复。你问的是：「{message}」。\n\n'
                     f'在真实环境中，这里会返回 LLM 生成的回答。\n'
                     f'当前阶段先理解 HTTP 请求→LLM→HTTP 响应这个链路即可。',
            "model": "mock-model-v0",
            "tokens_used": 0,
        },
        "note": "这是一个 mock 端点，不调用真实 LLM，用于理解 API 结构和数据流"
    }


# ============================================================
# 4. 启动说明
# ============================================================
# 在终端执行：
#   source ~/miniconda3/bin/activate agent-learn
#   cd ~/Agent/agent-learn/week01-basics
#   uvicorn main:app --reload --host 0.0.0.0 --port 8000
#
# 然后：
#   - 浏览器打开 http://localhost:8000/docs   → 自动生成的交互式 API 文档
#   - curl http://localhost:8000/              → 根路径
#   - curl http://localhost:8000/health         → 健康检查
#   - curl http://localhost:8000/hello/小明     → 路径参数
#   - curl "http://localhost:8000/search?q=agent" → 查询参数
#   - curl -X POST http://localhost:8000/chat  → POST 聊天（需 API key）
#     -H "Content-Type: application/json"
#     -d '{"message": "什么是 Agent？用一句话解释"}'
#
# ⚠️ 聊天端点需要设置环境变量：export OPENAI_API_KEY="sk-xxx"
# 如果没有 API key，可以先跑其他端点，聊天端点后面接入本地模型再测。
