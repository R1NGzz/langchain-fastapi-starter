"""
RAG 引擎 —— 检索+生成逻辑。

注意：重量级对象（embeddings / vector_store / model）用懒加载——
服务启动时不初始化，第一个请求来了才加载。否则 uvicorn 启动超时。
"""
import os
import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

logger = logging.getLogger(__name__)

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")

# ---- 懒加载：首次使用时才初始化 ----
_embeddings = None
_vector_store = None
_model = None


def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        from langchain_huggingface import HuggingFaceEmbeddings
        _embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-zh-v1.5",
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings


def _get_model():
    global _model
    if _model is None:
        from langchain.chat_models import init_chat_model
        _model = init_chat_model(
            "claude-sonnet-4-6",
            api_key=os.getenv("ANTHROPIC_AUTH_TOKEN") or os.getenv("ANTHROPIC_API_KEY"),
        )
    return _model


def _get_vector_store():
    global _vector_store
    if _vector_store is None and os.path.isdir(CHROMA_DIR) and os.listdir(CHROMA_DIR):
        from langchain_chroma import Chroma
        _vector_store = Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=_get_embeddings(),
        )
        logger.info("向量库已加载: %s", CHROMA_DIR)
    return _vector_store


# ═══════════════════════════════════════════════════
# 问答
# ═══════════════════════════════════════════════════

def ask_rag(question: str, k: int = 15) -> dict:
    """返回 {"answer": str, "sources": [{"page": ..., "content": ...}]}"""
    vs = _get_vector_store()
    if vs is None:
        return {"answer": "向量库为空，请先上传 PDF。", "sources": [], "question": question}

    # 1. 检索
    raw = vs.similarity_search(question, k=k)

    # 2. 去重
    seen, docs = set(), []
    for d in raw:
        key = d.page_content.strip()
        if key not in seen:
            seen.add(key)
            docs.append(d)

    # 3. 拼 RAG prompt
    ctx = "\n\n".join(f"[{i+1}] {d.page_content}" for i, d in enumerate(docs))
    prompt = (
        "你是一个文档问答助手。请严格根据以下资料回答问题。\n"
        '如果资料中没有答案，请明确说"文档中未提及"，不要编造。\n\n'
        f"资料：\n{ctx}\n\n"
        f"问题：{question}"
    )

    # 4. LLM
    model = _get_model()
    result = model.invoke(prompt)
    raw_content = result.content
    if isinstance(raw_content, list):
        answer = "".join(b["text"] for b in raw_content if b.get("type") == "text")
    else:
        answer = raw_content

    sources = [{"page": d.metadata.get("page"), "content": d.page_content} for d in docs]
    logger.info("RAG 完成: '%s...' → %d sources", question[:40], len(sources))
    return {"answer": answer, "sources": sources, "question": question}


# ═══════════════════════════════════════════════════
# PDF 入库
# ═══════════════════════════════════════════════════

def ingest_pdf(file_path: str) -> int:
    """加载 PDF → 切分 → 向量化 → 入库，返回 chunk 数"""
    global _vector_store
    from langchain_chroma import Chroma

    loader = PyPDFLoader(file_path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=50,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )
    chunks = splitter.split_documents(docs)

    # 清空旧库，避免不同 PDF 数据混在一起
    import shutil
    if os.path.isdir(CHROMA_DIR):
        shutil.rmtree(CHROMA_DIR)

    _vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=_get_embeddings(),
        persist_directory=CHROMA_DIR,
    )
    logger.info("入库完成: %d chunks → %s", len(chunks), CHROMA_DIR)
    return len(chunks)
