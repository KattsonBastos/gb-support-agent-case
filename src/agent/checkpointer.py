"""Ciclo de vida do Checkpointer do LangGraph (Redis com fallback para MemorySaver) - ADR-001."""

import logging
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Any, AsyncIterator, Dict, Optional

from src.agent.graph import reset_compiled_graph, set_compiled_graph
from src.core.config import settings

logger = logging.getLogger(__name__)


def _ttl_config() -> Optional[Dict[str, Any]]:
    """Monta a configuração de TTL das sessões no Redis (minutos, renovado a cada leitura)."""
    if settings.CHECKPOINT_TTL_MINUTES <= 0:
        return None
    return {"default_ttl": settings.CHECKPOINT_TTL_MINUTES, "refresh_on_read": True}


@asynccontextmanager
async def checkpointer_lifespan() -> AsyncIterator[None]:
    """Inicializa o grafo com AsyncRedisSaver quando `REDIS_URL` estiver configurada.

    - Sem `REDIS_URL`: mantém o `MemorySaver` preguiçoso de `get_compiled_graph()` (testes/dev).
    - Redis indisponível na subida: registra aviso e degrada para `MemorySaver`,
      para que o atendimento não seja interrompido.
    """
    if not settings.REDIS_URL:
        logger.info("REDIS_URL não configurada; utilizando MemorySaver para o estado das sessões.")
        yield
        return

    async with AsyncExitStack() as stack:
        try:
            from langgraph.checkpoint.redis.aio import AsyncRedisSaver

            saver = await stack.enter_async_context(
                AsyncRedisSaver.from_conn_string(settings.REDIS_URL, ttl=_ttl_config())
            )
        except Exception as exc:
            # A URL pode conter credenciais: registra apenas o tipo do erro.
            logger.warning(
                "Redis indisponível (%s); degradando para MemorySaver.", type(exc).__name__
            )
            saver = None

        if saver is not None:
            set_compiled_graph(saver)
            logger.info("Checkpointer Redis inicializado para o estado das sessões.")

        try:
            yield
        finally:
            reset_compiled_graph()
