import os
import asyncio
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, AIMessage, SystemMessage
from langchain.tools import tool
from pydantic import BaseModel, Field
				
class MovieInfo(BaseModel):
    """电影信息结构化模板"""
    title: str = Field(description="电影名称")
    year: int = Field(description="上映年份")
    director: str = Field(description="导演姓名")
    score: float = Field(description="豆瓣评分")

api_key = os.getenv("ANTHROPIC_API_KEY")

@tool
def get_weather(location:str)->str:
    """查询指定城市天气"""
    return f"{location}当前天气晴朗"
model = init_chat_model(
    "claude-sonnet-4-6",
    temperature=0.7,
    timeout=30,
    max_tokens=1000,
    max_retries=6,
    thinking={"type": "disabled"}
    )

#绑定结构化格式


print(model.profile)
# 包含最大上下文长度、是否支持图片输入、推理能力、工具调用支持等信息