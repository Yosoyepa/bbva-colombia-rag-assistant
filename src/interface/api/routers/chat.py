"""Router de conversación RAG (CU-02/CU-03)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from src.interface.api.dependencies import get_container
from src.interface.api.schemas import ChatRequest, ChatResponse
from src.interface.container import Container

router = APIRouter(tags=["chat"])


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
    )
