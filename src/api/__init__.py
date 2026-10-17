"""Módulo da API HTTP (FastAPI, schemas e rotas)."""

from src.api.routes import router
from src.api.schemas import ChatRequest, ChatStreamChunk

__all__ = ["router", "ChatRequest", "ChatStreamChunk"]
