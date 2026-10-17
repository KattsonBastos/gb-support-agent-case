"""Rotas da API de Suporte à Revendedora GB."""

import asyncio
from typing import AsyncGenerator
from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse

from src.api.schemas import ChatRequest, ChatStreamChunk

router = APIRouter(prefix="/api/v1", tags=["Chat"])


async def mock_chat_stream_generator(request: ChatRequest) -> AsyncGenerator[str, None]:
    """Gerador assíncrono mockado para simulação de streaming SSE.

    Emite a frase 'Teste de streaming SSE' palavra por palavra com intervalo
    de 0.5s entre cada emissão, respeitando estritamente o protocolo SSE.
    """
    words = ["Teste", " de", " streaming", " SSE"]

    for word in words:
        chunk = ChatStreamChunk(chunk=word)
        yield chunk.to_sse()
        await asyncio.sleep(0.5)


@router.post(
    "/chat/stream",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
    summary="Streaming de resposta do assistente (SSE)",
    description=(
        "Recebe a mensagem da revendedora com isolamento por session_id e CPF opcional, "
        "retornando os chunks de resposta via Server-Sent Events (SSE)."
    ),
    responses={
        200: {
            "description": "Fluxo de eventos Server-Sent Events",
            "content": {"text/event-stream": {}},
        },
        422: {
            "description": "Erro de validação nos campos de entrada (session_id inválido ou CPF malformado)",
        },
    },
)
async def chat_stream_endpoint(request: ChatRequest) -> StreamingResponse:
    """Endpoint principal de chat com resposta em streaming Server-Sent Events (SSE)."""
    headers = {
        "Content-Type": "text/event-stream; charset=utf-8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }

    return StreamingResponse(
        mock_chat_stream_generator(request),
        media_type="text/event-stream",
        headers=headers,
    )
