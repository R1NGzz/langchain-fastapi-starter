# Naive RAG API

基于 FastAPI + ChromaDB + DeepSeek 的端到端 RAG 文档问答系统。

## 架构

```
curl POST /rag/ask {"question": "xxx"}
    │
    ▼
┌─────────────────────────────────────────┐
│  FastAPI (app/main.py)                   │
│  include_router(rag.router)              │
└──────────────┬──────────────────────────┘
               │
    ┌──────────▼──────────┐
    │  routers/rag.py     │  ← HTTP 层：收请求、验参数、返回 JSON
    │  POST /rag/ask       │
    │  POST /rag/upload     │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │  rag_engine.py       │  ← 业务层：检索、去重、调 LLM
    │  ask_rag()           │
    │  ingest_pdf()         │
    └──────┬──────┬────────┘
           │      │
    ┌──────▼──┐ ┌─▼──────────┐
    │ ChromaDB │ │ LLM (DeepSeek)│
    │ + BGE    │ │ Anthropic API │
    │ 向量检索  │ │               │
    └──────────┘ └──────────────┘
```

## 技术栈

| 层 | 技术 |
|----|------|
| API | FastAPI + Pydantic |
| LLM | DeepSeek (Anthropic 兼容端点) |
| 向量化 | BAAI/bge-small-zh-v1.5 (HuggingFace) |
| 向量库 | ChromaDB (持久化) |
| 文档解析 | PyPDFLoader |
| 切分 | RecursiveCharacterTextSplitter (chunk=1000, overlap=50) |

## 快速启动

```bash
# 1. 环境
source ~/miniconda3/bin/activate agent-learn
pip install -r requirements.txt

# 2. 设置 API Key
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="sk-xxx"

# 3. 启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 使用

```bash
# 上传 PDF
curl -X POST http://localhost:8000/rag/upload \
  -F "file=@your_document.pdf"

# 文档问答
curl -X POST http://localhost:8000/rag/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "这篇论文的主要贡献是什么？"}'
```

## API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 健康检查 |
| `/rag/upload` | POST | 上传 PDF，自动切分+向量化+入库 |
| `/rag/ask` | POST | 文档问答（含引用来源页码） |
| `/chat/` | POST | Agent 对话（Week1 遗留） |
| `/docs` | GET | Swagger 交互式文档 |

## 已知局限（Week 2 Naive RAG 天花板）

- 纯向量检索对中英混合文档命中不准（参考文献页抢结果）
- 无混合检索 / Reranker（Week 3 会学）
- 不支持多轮对话（Week 3 会加 Memory）

## 项目结构

```
app/
├── main.py            # FastAPI 入口 + 注册路由
├── rag_engine.py      # RAG 核心逻辑（检索/去重/LLM）
├── routers/
│   ├── chat.py        # /chat Agent 端点（Week1）
│   └── rag.py         # /rag/ask + /rag/upload
└── schemas/
    ├── chat.py        # ChatRequest/ChatResponse
    └── rag.py         # AskRequest/AskResponse/SourceDoc
```
