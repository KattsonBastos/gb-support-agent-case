"""Ponto de entrada principal da aplicação FastAPI - Agente GB."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.agent.checkpointer import checkpointer_lifespan
from src.api.routes import router as chat_router, web_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Inicializa e encerra recursos compartilhados (checkpointer Redis das sessões)."""
    async with checkpointer_lifespan():
        yield


app = FastAPI(
    title="GB Revendedora Support Agent API",
    description="Motor transacional e de suporte à Revendedora Boticário baseado em IA e LangGraph.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configuração de CORS para permitir consumo pelo simulador/frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro das rotas da API e Simulador Web
app.include_router(chat_router)
app.include_router(web_router)


@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint de verificação de integridade da API."""
    return {"status": "ok", "service": "gb-support-agent"}
