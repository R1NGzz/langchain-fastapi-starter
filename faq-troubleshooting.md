# Week 01 — FAQ & 踩坑记录

> 本文件记录了 Day 1 学习过程中遇到的经典问题及解决方案，供后续回顾参考。

---

## 问题索引


| #  | 问题                                                | 关键词              |
| -- | --------------------------------------------------- | ------------------- |
| 1  | `fastapi: command not found`                        | 环境激活            |
| 2  | `Could not find a default file to run`              | entrypoint 配置     |
| 3  | 如何在`pyproject.toml` 中配置应用入口               | entrypoint          |
| 4  | 部署失败：`Metadata field Name not found`           | build-system        |
| 5  | 部署失败：`Unable to determine which files to ship` | setuptools vs hatch |
| 6  | 如何访问 FastAPI Cloud 部署好的地址                 | 部署 URL            |
| 7  | 部署后页面无法访问：`fastapi[standard]`             | 依赖配置            |
| 8  | `GET /chat` 返回 405 Method Not Allowed             | POST vs GET         |
| 9  | Pydantic 字段名拼错导致 500                         | 字段一致性          |
| 10 | POST 请求体 JSON 格式错误（422）                    | JSON 语法           |
| 11 | `response_model` 到底能防什么、不能防什么           | 出口校验            |

---

## 1. `fastapi: command not found`（环境未激活）

### 现象

```bash
$ fastapi dev
fastapi: command not found
```

### 原因

conda 创建的虚拟环境没有激活，shell 找不到 `fastapi` 命令。

### 解决

```bash
source ~/miniconda3/bin/activate agent-learn
```

验证：

```bash
which python    # 应显示 agent-learn 环境下的路径
pip list | grep fastapi
```

### 知识点

- **conda 环境隔离**：每个项目的依赖装在独立环境中，不会互相污染
- 任何时候打开新终端，都要先 `activate`

---

## 2. `fastapi dev` 找不到默认文件

### 现象

```
FastAPI   Starting development server 🚀

Could not find a default file to run, please provide an explicit path
```

### 原因

`fastapi dev` 没有指定要跑哪个 `.py` 文件，也没在 `pyproject.toml` 里配入口。

### 解决方案一：命令行指定文件

```bash
fastapi dev main.py
```

### 解决方案二：配置 `pyproject.toml`（推荐）

```toml
[tool.fastapi]
entrypoint = "main:app"
```

配置后直接 `fastapi dev` 就能跑。

### 知识点

- `main:app` 的含义：`main` = `main.py`，`app` = 文件里 `app = FastAPI()` 的变量名
- 这和 `uvicorn main:app` 是同一套语法

---

## 3. 如何在 `pyproject.toml` 中配置应用入口

> 这是 `fastapi dev` 自动发现项目的基础配置。

```toml
[tool.fastapi]
entrypoint = "main:app"
```

- `[tool.fastapi]` — FastAPI CLI 专用的配置段
- `entrypoint = "main:app"` — `<文件名>:<FastAPI 实例变量名>`

配置后等价于每次自动执行 `uvicorn main:app`。

---

## 4. 部署失败：`Metadata field Name not found`

### 现象

```
❌ Build failed

error: Failed to parse metadata from built wheel
  Caused by: Metadata field Name not found
```

### 原因

`pyproject.toml` 只有 `[tool.fastapi]`，缺少：

- `[build-system]` — 告诉构建工具（pip/uv）如何构建项目
- `[project]` — 项目基本元数据（最关键是 `name`）

部署平台会把你的代码打成 wheel 包，缺少 `name` 元数据直接失败。

### 解决：补全三段式 pyproject.toml

```toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[project]
name = "agent-learning-week1"
version = "0.1.0"
description = "Agent Learn - Week 1"
requires-python = ">=3.11"
dependencies = [
    "fastapi[standard]>=0.137",
    "uvicorn>=0.49",
    "openai>=2.0",
    "pydantic>=2.0",
]

[tool.fastapi]
entrypoint = "main:app"
```

### 知识点


| 段               | 作用                  | 谁用                          |
| ---------------- | --------------------- | ----------------------------- |
| `[build-system]` | 定义构建工具          | pip / uv / 部署平台           |
| `[project]`      | 项目元数据 + 依赖列表 | pip / uv / 部署平台           |
| `[tool.fastapi]` | FastAPI CLI 专用配置  | `fastapi dev` / `fastapi run` |

---

## 5. 部署失败：`Unable to determine which files to ship`

### 现象

```
ValueError: Unable to determine which files to ship inside the wheel
using the following heuristics: ...

The most likely cause of this is that there is no directory that matches
the name of your project (agent_learning_week1).
```

### 原因

默认构建工具 **Hatch** 查找和项目名匹配的目录（如 `agent_learning_week1/`），但我们的项目是 **单文件平铺结构**（`main.py` 直接放在根目录），没有这样的目录。

### 解决：换用 setuptools + `py-modules`

```toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
py-modules = ["main", "main_ref"]
```

### 知识点


| 构建工具       | 适用场景                     |     单文件项目支持     |
| -------------- | ---------------------------- | :---------------------: |
| **hatchling**  | 标准包目录结构（`src/pkg/`） |      ❌ 需额外配置      |
| **setuptools** | 老牌构建工具，灵活           | ✅`py-modules` 原生支持 |

- `py-modules`：告诉 setuptools 这些是**独立 .py 模块**，不是包目录
- 如果项目是 `src/agent/pkg/__init__.py` 结构，应该用 `packages` 而不是 `py-modules`

---

## 6. 如何访问 FastAPI Cloud 部署好的地址

### 方法：CLI 查 JSON

```bash
# 查看当前目录链接的应用信息（含 URL）
fastapi cloud apps get --json
```

输出示例：

```json
{
  "data": {
    "app": {
      "slug": "agentlearning-week1-first-app",
      "url": "https://agentlearning-week1-first-app.fastapicloud.dev"
    }
  }
}
```

### URL 规律

FastAPI Cloud 的 URL 格式：

```
https://<app-slug>.fastapicloud.dev
```

`app-slug` 是 `app-name` 的规范化版本（驼峰→连字符，下划线→连字符）。

### 其他常用命令

```bash
fastapi cloud apps get --json          # 查看应用信息
fastapi cloud deployments list --json  # 查看部署历史
fastapi cloud logs                     # 查看运行时日志
fastapi cloud env set KEY VALUE        # 设置环境变量
```

---

## 7. 部署后页面无法访问：`fastapi[standard]` 缺失

### 现象

浏览器访问部署地址显示找不到页面，或者 `fastapi cloud logs` 显示：

```
RuntimeError: To use the fastapi command, please install "fastapi[standard]":
    pip install "fastapi[standard]"

Traceback (most recent call last):
  File "/app/.venv/bin/fastapi", line 10, in <module>
    sys.exit(main())
  File "/app/.venv/lib/python3.14/site-packages/fastapi/cli.py", line 12, in main
    raise RuntimeError(message)
```

应用反复重启，每次都是同一个错误。

### 原因

FastAPI Cloud 平台使用 `fastapi` CLI 命令启动服务（`fastapi run` 或 `fastapi dev`），这需要 `fastapi[standard]` 这个 **extra**。普通的 `fastapi` 包**不包含 CLI 运行时所需的全部依赖**（如 `uvicorn`、`fastapi-cli` 等）。

pyproject.toml 里写的是：

```toml
dependencies = [
    "fastapi>=0.137",   # ❌ 缺 [standard] extra
]
```

### 解决

```toml
dependencies = [
    "fastapi[standard]>=0.137",   # ✅ 加上 [standard]
]
```

### 知识点

- **`fastapi` vs `fastapi[standard]`**：
  - `fastapi` — 核心框架，不含 uvicorn 等
  - `fastapi[standard]` — 加装全栈依赖（uvicorn、fastapi-cli、httpx 等）
- **本地 OK ≠ 部署 OK**：本地可能手动装过 uvicorn，但部署时只读 pyproject.toml 来决定装什么
- **pyproject.toml 的 `dependencies` 是部署的唯一真相源**

---

## 8. `GET /chat` 返回 405 Method Not Allowed

### 现象

```
127.0.0.1:61949 - "GET /chat HTTP/1.1" 405
```

### 原因

浏览器地址栏直接敲回车、或者点了链接，默认发的是 **GET** 请求。但 `/chat` 端点是 `@app.post("/chat")`，只接受 **POST**。

### 解决

POST 端点的三种正确测试方式：

**① Swagger 文档（最方便）**

```
http://localhost:8000/docs → 找到 POST /chat → Try it out → Execute
```

**② curl**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'
```

**③ VS Code 插件**：Thunder Client / REST Client

### 知识点


| HTTP 方法 | 数据在哪            | 怎么触发                           |
| --------- | ------------------- | ---------------------------------- |
| **GET**   | URL（`?key=value`） | 浏览器地址栏、`<a>` 链接           |
| **POST**  | 请求体（JSON）      | 表单提交、API 调用、`curl -X POST` |

- **405 = Method Not Allowed**：路径对了，方法不对
- **404 = Not Found**：路径就不对

---

## 9. Pydantic 字段名拼错导致 500

### 现象

```python
class chatresponse(BaseModel):
    repaly: str     # ← 拼错了，是 r-e-p-a-l-y

@app.post("/chat", response_model=chatresponse)
async def chat(request: chatrequest):
    return chatresponse(
        reply=f"..."  # ← 用的是 reply，和类里的 repaly 对不上 → 500
    )
```

### 原因

Pydantic 对象构造时字段名严格匹配。`reply` 在 `chatresponse` 里不存在 → 构造失败 → 500。

### 解决

保持类定义和构造函数**字段名完全一致**：

```python
class ChatResponse(BaseModel):
    reply: str          # ✅ 正确拼写

# ...
return ChatResponse(reply=f"...")  # ✅ 两边一致
```

### 知识点

- Pydantic 构造对象时，字段名是**精确匹配**，不会模糊纠正
- 这类错误 IDE 不一定能发现（字符串匹配的局限性）
- Python 惯例：类名 **PascalCase**（`ChatRequest`），字段名 **snake_case**（`reply`）

---

## 10. POST 请求 JSON 格式错误（422）

### 现象

```json
{
  "detail": [
    {
      "type": "json_invalid",
      "loc": ["body", 19],
      "msg": "JSON decode error",
      "ctx": {
        "error": "Expecting ',' delimiter"
      }
    }
  ]
}
```

### 原因

请求体 JSON 语法错误，最常见的是两个字段之间漏了逗号：

```json
// ❌ 字段之间没写逗号
{"message": "你好" "temperature": 0.7}

// ✅ 正确
{"message": "你好", "temperature": 0.7}
```

### 解决

在 `/docs` 页面填写 Request body 更不容易出错：

```json
{
  "message": "你好"
}
```

### 知识点

- `422 Unprocessable Entity` = 请求格式正确（HTTP 层面），但**内容不合规**（语义层面）
- 和 405 区别：405 = 方法错，422 = 数据格式/校验错
- Swagger `/docs` 自动生成请求模板，填入即可，降低手工拼 JSON 的错误率

---

## 11. `response_model` 到底能防什么、不能防什么

### 核心结论

`response_model` 是**出口守卫**，不是**内部质量检查**——它校验你 return 出去的东西，不校验你怎么构造它。

### ✅ 能防的


| 场景                   | 说明                                       |
| ---------------------- | ------------------------------------------ |
| 返回裸 dict 时字段拼错 | dict 不校验，漏到 response_model 才被发现  |
| 返回对象带多余敏感字段 | 自动裁剪，只保留 response_model 定义的字段 |
| 返回值类型不对         | 校验+报错                                  |

```python
# ✅ 防住了：返回 dict 时字段拼错
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    return {"repaly": "..."}   # ← 没人拦住这个 dict
    # response_model 校验 → 发现 repaly 不在 ChatResponse 中 → 报错
```

### ❌ 防不了的


| 场景                             | 为什么                                               |
| -------------------------------- | ---------------------------------------------------- |
| 自己构造 Pydantic 对象时字段拼错 | 炸在 Python/Pydantic 构造函数，到不了 response_model |

```python
# ❌ 防不了：炸在 Pydantic 对象构造
return ChatResponse(repaly="...")  # ← Python 直接抛 TypeError，response_model 没机会执行
```

### 知识点

```
return 对象 → response_model 校验 → 序列化 JSON → 发给客户端
           ↑                                ↑
    炸在这里，response_model 管不了    炸在这里，response_model 能管
```

- `response_model` 在**序列化阶段**生效，不在**函数体内**生效
- 自己返回 Pydantic 对象 = 自带校验，但拼错字段会 500
- 返回 dict + response_model = 双重保险

---

---

## Day 2 — 工程化重构

### 12. 相对导入 `from .routers import chat` 报 `ImportError`

**现象**：

```
ImportError: attempted relative import with no known parent package
```

**原因**：直接 `python app/main.py` 运行时，Python 不认为 `app/` 是一个包，`.` 相对导入失效。

**解决**：用 `uvicorn` 启动，它会正确处理包结构：

```bash
uvicorn app.main:app --reload
```

**知识点**：
- `.` = 从当前包开始找，`..` = 上一层包
- 相对导入只在包（package）上下文里有效
- 永远用 `uvicorn` 启动 FastAPI 项目，不要 `python xxx.py`

---

### 13. 启动命令换了：`main:app` → `app.main:app`

**原因**：Day 2 重构后，`app = FastAPI()` 从 `main.py` 移到了 `app/main.py`。

**知识**：`uvicorn <模块路径>:<实例名>`，模块路径用 `.` 分隔目录。

---

## Day 3-4 — LangChain + DeepSeek 踩坑

### 14. `init_chat_model("claude-sonnet-4-6")` 怎么知道 DeepSeek 地址？

**答案**：读取环境变量。DeepSeek Anthropic 端点需要两个：

```bash
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_API_KEY="sk-xxx"
```

**注意**：DeepSeek 的 Anthropic 端点和 OpenAI 端点**不是同一套环境变量**。混用会报认证错误。

---

### 15. LangChain 文档 v1.0 大改——新旧 API 混淆

**现象**：跟旧版教程写 `from langchain.prompts import ChatPromptTemplate` → 找不到，或者 API 签名不一样。

**原因**：`docs.langchain.com`（新版）入口是 `create_agent` + `@tool`；旧版 `python.langchain.com/v0.1/` 才有六大模块和 LCEL。

**对策**：
- 学概念看旧版（面试考）
- 写代码用新版（`create_agent`、`init_chat_model`、`stream_events v3`）

---

### 16. `langchain.agents` vs `langchain.chat_models` 导入路径

新版导入：

```python
from langchain.agents import create_agent       # Agent
from langchain.chat_models import init_chat_model  # 模型
from langchain.tools import tool                # @tool 装饰器
```

不需要单独装 `langchain-openai` / `langchain-anthropic` — `init_chat_model` 根据模型名字符串自动选。

---

## Day 6 — FastAPI + LangChain 整合踩坑

### 17. `agent.invoke()` 报 `ValidationError: reply - Input should be a valid string`

**现象**：

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for ChatResponse
reply
  Input should be a valid string [type=string_type, input_value=[{...}, {...}], input_type=list]
```

**原因**：DeepSeek 返回的 `AIMessage.content` 不是纯字符串，是一个列表：

```python
[
    {"type": "reasoning", "reasoning": "...", "signature": "xxx"},
    {"type": "text", "text": "北京今天晴，25°C"}
]
```

`ChatResponse.reply: str` 要求字符串，收到 list → 校验失败。

**解决**：

```python
last_msg = result["messages"][-1]
if isinstance(last_msg.content, list):
    reply_text = "".join(
        b["text"] for b in last_msg.content if b.get("type") == "text"
    )
else:
    reply_text = last_msg.content
```

**知识点**：
- `.content` → 可能返回 str 或 list（取决于模型/端点）
- `.content_blocks` → 永远返回 list
- DeepSeek Anthropic 端点返回包含 `reasoning` 和 `text` 两类块的列表
- 写 Agent 服务时**防御性判断 `isinstance(content, list)`** 是必要的

---

### 18. `agent.invoke()` 不能传字符串，`model.invoke()` 可以

```python
# ✅ model.invoke 接受字符串
model.invoke("你好")

# ❌ agent.invoke 不接受字符串，必须是 {"messages": [...]}
agent.invoke({"messages": [{"role": "user", "content": "你好"}]})
```

**原因**：Agent 底层是 LangGraph 状态图，入参必须是完整的状态字典（含 `messages` 键）。Model 是底层裸接口，宽松得多。

---

### 19. Agent 实例应该放在模块级，不是函数内

```python
# ✅ 正确：模块级，启动时创建一次
agent = create_agent(model=..., tools=[...])

@router.post("/")
async def chat(request: ChatRequest):
    result = agent.invoke(...)

# ❌ 错误：每次请求重新创建（200-500ms 开销）
@router.post("/")
async def chat(request: ChatRequest):
    agent = create_agent(model=..., tools=[...])  # 每次请求都编译图
```

**原因**：`create_agent` 内部编译 LangGraph 图，耗时 200-500ms。放模块级只编译一次。

---

## Day 7 — Git

### 20. `git branch -m main` 在空仓库报错

**现象**：

```
error: refname refs/heads/master not found
fatal: Branch rename failed
```

**原因**：改名必须在第一次 commit 之后，commit 之前分支还不存在。

**解决**：先 commit 再改名：

```bash
git add -A
git commit -m "first commit"
git branch -m main
```

---

## 总结：Day 1 部署踩坑全景

```
开发者写 main.py
      │
      ▼
配置 pyproject.toml ── 三段式：build-system + project + tool.fastapi
      │
      ├── [build-system] 用 setuptools（单文件项目比 hatch 友好）
      ├── [project] 必须含 name、version、dependencies
      │    └── fastapi[standard] ← 一定要写 [standard]！
      └── [tool.fastapi] entrypoint = "main:app"
      │
      ▼
fastapi deploy ── 打包 → 构建镜像 → 部署 → ✅ 可访问
                                           │
                                    https://<slug>.fastapicloud.dev
```


## 一句话区分FastAPI和LangChain

```
FastAPI  = 对外的门面（HTTP 请求进来 → JSON 响应出去）
LangChain = 对内的脑子（调用 LLM、串联 prompt、管理工具）
```

---

### 你已经在用的例子

你的 Day 2 项目就是典型：

```
用户浏览器
    │  POST /chat  {"message": "今天天气？"}
    ▼
┌─────────────────────────────┐
│  FastAPI（门面层）           │
│  - 接收 HTTP 请求            │
│  - Pydantic 校验数据         │
│  - 路由到 chat 端点          │
│  - 返回 JSON 响应            │
│           │                 │
│           ▼                 │
│  LangChain（脑子层）         │
│  - Prompt 模板              │
│  - 调用 LLM                 │
│  - 解析输出                 │
│  - 管理工具调用              │
└─────────────────────────────┘
```

**FastAPI 管的事**：网络、路由、校验、序列化——跟 LLM 无关 **LangChain 管的事**：prompt 拼装、调哪个模型、工具调用、记忆——跟 HTTP 无关

---

### 面试能这样讲的关系图

```
FastAPI  ←→  LangChain
   │             │
 门面层        逻辑层
   │             │
 HTTP 协议     LLM 编排
 路由分发      模型选择
 数据校验      Prompt 模板
 序列化        工具调用
 中间件        记忆管理
   │             │
   └──────┬──────┘
          │
    用户请求进来 → FastAPI 预处理 → LangChain 做推理 → FastAPI 返回结果
```

---

### 关键点：互不绑定

* 你不用 FastAPI 也能用 LangChain——写个 Python 脚本直接 `.invoke()`
* 你不用 LangChain 也能用 FastAPI——直接 `openai` SDK 调 LLM，或者不调 LLM
* 放一起只是因为你做的 **Agent 是一个 Web 服务**，需要 HTTP 对外 + LLM 对内


## LLM 层 stream vs Agent 层 stream\_events

```
┌─────────────────────────────────────────────┐
│  Agent 层  stream_events(version="v3")      │  ← 你写的这个
│  ┌─────────────────────────────────────┐    │
│  │  LLM 层  stream=True                 │    │
│  │  "我" "需要" "查" "天" "气" ...     │    │
│  │  ↑ 逐 token 返回                     │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  还额外暴露这些事件：                          │
│  - 🔧 tool_call_start → 准备调 get_weather  │
│  - 🔧 tool_call_end   → 工具返回结果         │
│  - 🧠 reasoning        → 模型思考过程        │
│  - 💬 text             → 最终文本            │
└─────────────────────────────────────────────┘
```


|            | LLM 层`stream=True`     | Agent 层`stream_events(v3)`            |
| ---------- | ----------------------- | -------------------------------------- |
| 粒度       | token 级别（单个词/字） | **事件**级别（思考、工具调用、文本块） |
| 能看到什么 | 只看到模型吐字          | 看到 Agent 的**每一步决策**            |
| 工具调用   | ❌ 看不到               | ✅`on_tool_start` / `on_tool_end`      |
| 用途       | 打字机效果              | 观察 Agent 行为 + 调试 + 复杂 UI       |

---

### 你代码里的实际效果

```python
stream = agent.stream_events(..., version="v3")

for msg in stream.messages:
    for word in msg.text:
        print(word, end="", flush=True)   # 也在逐字打，但 msg 可能是不同类型
```

迭代时 `stream.messages` 里不只有文本——还有 `ToolMessage`、`ReasoningMessage` 等。你只处理了 `.text`，其实还能拿到工具调用信息。

---

### 一句话总结

> LLM stream = 逐 token 看 LLM "说"了什么 Agent stream\_events = 逐事件看 Agent "做"了什么（思考 → 调工具 → 拿结果 → 说回复）

后面做项目时，Agent stream 让你能在 UI 上展示 "🔍 正在搜索..." → "📄 找到 3 条结果" → "✍️ 正在生成回答..." 这样的过程，而不只是一个转圈。
