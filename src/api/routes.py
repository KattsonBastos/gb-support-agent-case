"""Rotas da API de Suporte à Revendedora GB com Streaming Real via LangGraph SSE."""

import json
import logging
from typing import AsyncGenerator, Optional
from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from langchain_core.messages import HumanMessage

from src.agent.graph import get_compiled_graph
from src.api.schemas import ChatRequest, ChatStreamChunk
from src.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Chat"])
templates = Jinja2Templates(directory="templates")

def _setup_langchain_compat():
    """Garante compatibilidade do CallbackHandler do Langfuse 2.x com Langchain 0.2+/1.x."""
    import sys
    import types
    if "langchain.callbacks.base" not in sys.modules:
        import langchain_core.callbacks.base
        mod = types.ModuleType("langchain.callbacks")
        mod_base = types.ModuleType("langchain.callbacks.base")
        mod_base.BaseCallbackHandler = langchain_core.callbacks.base.BaseCallbackHandler
        sys.modules["langchain.callbacks"] = mod
        sys.modules["langchain.callbacks.base"] = mod_base

    if "langchain.schema.agent" not in sys.modules:
        mod_schema = types.ModuleType("langchain.schema")
        mod_agent = types.ModuleType("langchain.schema.agent")
        mod_doc = types.ModuleType("langchain.schema.document")
        from langchain_core.documents import Document
        from langchain_core.agents import AgentAction, AgentFinish
        mod_agent.AgentAction = AgentAction
        mod_agent.AgentFinish = AgentFinish
        mod_doc.Document = Document
        sys.modules["langchain.schema"] = mod_schema
        sys.modules["langchain.schema.agent"] = mod_agent
        sys.modules["langchain.schema.document"] = mod_doc


def _get_langfuse_callback(session_id: str, user_id: Optional[str] = None):
    """Instancia dinamicamente o LangfuseCallbackHandler conforme a spec 06-observabilidade.md."""
    import os
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST", "http://langfuse:3000")

    if not public_key or not secret_key:
        return None

    try:
        _setup_langchain_compat()
        from langfuse.callback import CallbackHandler
        return CallbackHandler(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
            session_id=session_id,
            user_id=user_id,
        )
    except Exception as exc:
        logger.warning(f"Não foi possível inicializar LangfuseCallbackHandler: {exc}")
        return None


def _flush_langfuse(handler=None):
    """Garante envio imediato dos traces do Langfuse ao final do streaming."""
    try:
        if handler:
            if hasattr(handler, "flush"):
                handler.flush()
            elif hasattr(handler, "_langfuse_client") and hasattr(handler._langfuse_client, "flush"):
                handler._langfuse_client.flush()
            elif hasattr(handler, "langfuse") and hasattr(handler.langfuse, "flush"):
                handler.langfuse.flush()
    except Exception:
        pass


def _sanitize_markdown_chunk(text: str) -> str:
    """Escapa cifrões ($) para evitar que renderizadores Markdown/KaTeX quebrem a exibição de moedas."""
    if not text:
        return ""
    import re
    return re.sub(r"(?<!\\)\$", r"\\$", text)


async def chat_event_streamer(request: ChatRequest) -> AsyncGenerator[str, None]:
    """Consome o grafo LangGraph em tempo real e transmite os tokens via SSE.

    Utiliza graph.astream_events(version='v2'), filtrando os nós internos de roteamento,
    injetando callbacks do LangFuse para observabilidade e emitindo exclusivamente os tokens
    de texto no formato:
    data: {"chunk": "..."}\n\n
    """
    graph = get_compiled_graph()

    callbacks = []
    langfuse_cb = _get_langfuse_callback(
        session_id=request.session_id,
        user_id=request.cpf,
    )
    if langfuse_cb:
        callbacks.append(langfuse_cb)

    config = {
        "configurable": {"thread_id": request.session_id},
        "callbacks": callbacks,
        "metadata": {
            "langfuse_session_id": request.session_id,
            "langfuse_user_id": request.cpf,
            "langfuse_trace_name": "gb-support-agent-chat",
        },
    }

    input_state = {
        "messages": [HumanMessage(content=request.message)],
        "session_id": request.session_id,
        "cpf": request.cpf,
        "contexto_recuperado": [],
        "tentativas_tool": 0,
    }

    try:
        async for event in graph.astream_events(input_state, config=config, version="v2"):
            kind = event.get("event")

            # Filtra eventos internos e extrai exclusivamente os chunks de texto do modelo de chat
            if kind == "on_chat_model_stream":
                chunk_obj = event.get("data", {}).get("chunk")
                if not chunk_obj:
                    continue

                content = chunk_obj.content

                # Se for texto direto (string não-vazia)
                if isinstance(content, str) and content:
                    chunk = ChatStreamChunk(chunk=_sanitize_markdown_chunk(content))
                    yield chunk.to_sse()

                # Se for lista de blocos com 'text'
                elif isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and part.get("text"):
                            chunk = ChatStreamChunk(chunk=_sanitize_markdown_chunk(part["text"]))
                            yield chunk.to_sse()
                        elif isinstance(part, str) and part:
                            chunk = ChatStreamChunk(chunk=_sanitize_markdown_chunk(part))
                            yield chunk.to_sse()

    except Exception as e:
        logger.error(f"Erro durante o streaming do LangGraph: {e}", exc_info=True)
        error_payload = json.dumps(
            {"chunk": f"\n\n[Erro no processamento da solicitação: {str(e)}]"},
            ensure_ascii=False,
        )
        yield f"data: {error_payload}\n\n"
    finally:
        if langfuse_cb:
            _flush_langfuse(langfuse_cb)


@router.post(
    "/chat/stream",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
    summary="Streaming de resposta do assistente via LangGraph (SSE)",
    description=(
        "Recebe a mensagem da revendedora com isolamento por session_id e CPF opcional. "
        "Executa o grafo ReAct (LangGraph) e retorna os tokens gerados em streaming SSE."
    ),
    responses={
        200: {
            "description": "Fluxo contínuo de Server-Sent Events (SSE)",
            "content": {"text/event-stream": {}},
        },
        422: {
            "description": "Erro de validação nos campos de entrada (session_id inválido ou CPF malformado)",
        },
    },
)
async def chat_stream_endpoint(request: ChatRequest) -> StreamingResponse:
    """Endpoint principal de chat integrado ao motor cognitivo LangGraph."""
    headers = {
        "Content-Type": "text/event-stream; charset=utf-8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }

    return StreamingResponse(
        chat_event_streamer(request),
        media_type="text/event-stream",
        headers=headers,
    )


# Rota web de demonstração/simulador
web_router = APIRouter(tags=["Web Simulator"])


@web_router.get("/", response_class=HTMLResponse, include_in_schema=False)
@web_router.get("/chat", response_class=HTMLResponse, include_in_schema=False)
async def chat_simulator_view(request: Request):
    """Renderiza a interface visual de simulação do chat da revendedora."""
    return templates.TemplateResponse(
        request=request,
        name="chat.html",
        context={"app_name": settings.APP_NAME},
    )


def __getattr__(name: str):
    """Permite inicialização direta via uvicorn src.api.routes:app conforme especificação de DevOps."""
    if name == "app":
        from src.main import app
        return app
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

