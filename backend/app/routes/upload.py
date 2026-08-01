import shutil
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import UPLOAD_DIR
from app.services.rag import RAGService

router = APIRouter(tags=["Upload"])


@router.post("/upload")
async def upload_documents(
    files: List[UploadFile] = File(...)
):
    if not files:
        raise HTTPException(
            status_code=400,
            detail="No files uploaded."
        )

    saved_files = []

    for file in files:

        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail=f"{file.filename} is not a PDF."
            )

        file_path = UPLOAD_DIR / file.filename

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        saved_files.append(file_path)

    # Lazy initialization (creates RAG service only when upload API is called)
    rag_service = RAGService()

    total_chunks = rag_service.index_documents(saved_files)

    return {
        "message": "Documents indexed successfully.",
        "documents": len(saved_files),
        "chunks": total_chunks,
        "uploaded_files": [file.name for file in saved_files]
    }