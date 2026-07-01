"""POST /rag/ask  +  POST /rag/upload"""
import os
import tempfile
import logging
from fastapi import APIRouter, UploadFile, File
from ..schemas.rag import AskRequest, AskResponse
from .. import rag_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    """文档问答——检索 PDF 内容 + LLM 生成回答"""
    result = rag_engine.ask_rag(request.question, k=10)
    return AskResponse(**result)


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    """上传 PDF，自动切分、向量化、入库"""
    # FastAPI UploadFile → 临时文件 → 调引擎入库 → 删临时文件
    suffix = os.path.splitext(file.filename or "upload.pdf")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        chunk_count = rag_engine.ingest_pdf(tmp_path)
        return {"status": "ok", "chunks": chunk_count, "filename": file.filename}
    finally:
        os.unlink(tmp_path)  # 用完删临时文件
