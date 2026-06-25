#数据模型独立出来
from pydantic import BaseModel, Field, field_validator

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    model: str = Field(default="claude-sonnet-4-6")

    @field_validator("message")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message 不能全为空格")
        return v.strip()
    
class ChatResponse(BaseModel):
    reply: str
    model: str