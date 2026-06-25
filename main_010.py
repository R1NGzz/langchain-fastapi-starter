from enum import Enum
from fastapi import FastAPI #===步骤1：导入FASTAPI
from pydantic import BaseModel, Field

class ModelName(str,Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"

class Item(BaseModel):
    name: str
    description:str | None = None
    price: float
    tax: float | None = None
    tags:list[str] = []

class chatrequest(BaseModel):#用户发来的聊天请求
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="用户输入的问题",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.1,
        le=2.0,
        description= "LLM随机性",
    )
    tags: list[str]= Field(
        default_factory=list,
        max_length=5,
    )
class chatresponse(BaseModel):#返回给用户的聊天响应
    reply: str

app = FastAPI(
    title="Agent Learn - Day 1",
    description="我的第一个 Agent API 服务",
    version="0.1.0",
) #===步骤2：创建fastlioAPI实例
@app.post("/chat", response_model=chatresponse)# 有 response_model=ChatResponse，就能1校验返回值，2. 过滤掉不该暴露的字段，3. 生成 API 文档（/docs 页面
async def chat(request:chatrequest):
    """收到消息，返回默认响应"""
    return chatresponse(
        reply=f"收到消息：【{request.message}】--没接入LLM前的固定回复"
    )
#--------------===步骤3：创建一个路径操作-------------------
@app.get("/") #@something 语法在 Python 中被称为「装饰器」。
#像一顶漂亮的装饰帽一样，将它放在一个函数的上方（我猜测这个术语的命名就是这么来的）。
#装饰器接收位于其下方的函数并且用它完成一些工作。

#@app就是告诉fastAPI在它下方的函数负责处理如下请求：
#请求路径为  /  
#使用  get 操作

async def root():#===步骤4：定义路径操作函数。这是一个python函数，每当FastAPI接收一个使用GET访问URL"/"时它就会被调用
    return {"message": "Hello World"}#===步骤5：返回内容

@app.get("/items/{item_id}")
async def read_user_item(
    item_id: str, needy: str, skip: int = 0, limit: int | None = None
):
    item = {"item_id": item_id, "needy": needy, "skip": skip, "limit": limit}
    return item

@app.get("/user/me")

async def read_inf():
    return {"user_id":"the current user"}

@app.get("/user/{user_id}")

async def get_id(user_id:int):
    return{"user_id":user_id}

@app.get("/model/{model_name}")

async def getmodelname(model_name:ModelName):
    if(model_name is ModelName.alexnet):
        return{"modelname":model_name,"ms": "deep learinign wtf"}
    if(model_name is ModelName.resnet):
        return{"modelname":model_name,"ms": "LeCNN"}
    if(model_name is ModelName.lenet):
        return{"modelname":model_name,"ms": "have some residuals"}
    
@app.get("/users/{user_id}/items/{item_id}")
async def read_user_item(
    user_id: int, item_id: str, q: str | None = None, short: bool = False
):
    item = {"item_id": item_id, "owner_id": user_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"}
        )
    return item

@app.get("/items/")
async def create_item(item:Item):
    
    return item