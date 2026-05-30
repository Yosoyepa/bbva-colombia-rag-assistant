"""Router de conversación RAG (CU-02/CU-03)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from src.interface.api.dependencies import get_container
from src.interface.api.schemas import ChatRequest, ChatResponse, RetrievalTraceItem
from src.interface.container import Container

router = APIRouter(tags=["chat"])


def _preview(text: str, max_chars: int = 260) -> str:
    clean = " ".join(text.split())
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 1].rstrip() + "…"


@router.post("/chat", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    container: Annotated[Container, Depends(get_container)],
) -> ChatResponse:
    """Responde una pregunta usando RAG y memoria por `session_id`."""
    answer = container.answer_use_case().execute(req.session_id, req.message)
    return ChatResponse(
        session_id=answer.session_id,
        content=answer.content,
        sources=answer.sources,
        retrieval_trace=[
            RetrievalTraceItem(
                rank=chunk.rank or index,
                source_url=chunk.source_url,
                distance=chunk.distance,
                similarity_score=chunk.similarity_score,
                rerank_score=chunk.rerank_score,
                content_preview=_preview(chunk.content),
            )
            for index, chunk in enumerate(answer.used_chunks, start=1)
        ],
    )
