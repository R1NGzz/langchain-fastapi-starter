"""RAG 相关 Pydantic 模型"""
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """POST /rag/ask 的请求体"""
    question: str = Field(..., min_length=1)


class SourceDoc(BaseModel):
    """单条检索来源"""
    page: int | None = None
    content: str


class AskResponse(BaseModel):
    """POST /rag/ask 的响应体"""
    answer: str
    sources: list[SourceDoc]   # 注意拼写：sources 不是 source
    question: str
