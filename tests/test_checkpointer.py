"""Testes do ciclo de vida do Checkpointer (Redis com fallback para MemorySaver) - ADR-001."""

from contextlib import asynccontextmanager
from unittest.mock import patch

import pytest
from langgraph.checkpoint.memory import MemorySaver

from src.agent import checkpointer as checkpointer_module
from src.agent import graph as graph_module
from src.core.config import settings


@pytest.fixture(autouse=True)
def _reset_graph():
    graph_module.reset_compiled_graph()
    yield
    graph_module.reset_compiled_graph()


class TestCheckpointerLifespan:
    """Valida a seleção do checkpointer sem acesso à rede."""

    @pytest.mark.asyncio
    async def test_sem_redis_url_usa_memory_saver(self, monkeypatch):
        monkeypatch.setattr(settings, "REDIS_URL", None)
        async with checkpointer_module.checkpointer_lifespan():
            graph = graph_module.get_compiled_graph()
            assert isinstance(graph.checkpointer, MemorySaver)

    @pytest.mark.asyncio
    async def test_com_redis_url_injeta_redis_saver(self, monkeypatch):
        monkeypatch.setattr(settings, "REDIS_URL", "redis://fake:6379")
        fake_saver = MemorySaver()  # substituto do AsyncRedisSaver (sem rede)
        chamadas = {}

        @asynccontextmanager
        async def fake_from_conn_string(url, ttl=None):
            chamadas["url"], chamadas["ttl"] = url, ttl
            yield fake_saver
            chamadas["fechado"] = True

        with patch(
            "langgraph.checkpoint.redis.aio.AsyncRedisSaver.from_conn_string",
            side_effect=fake_from_conn_string,
        ):
            async with checkpointer_module.checkpointer_lifespan():
                assert graph_module.get_compiled_graph().checkpointer is fake_saver

        assert chamadas["url"] == "redis://fake:6379"
        assert chamadas["ttl"]["default_ttl"] == settings.CHECKPOINT_TTL_MINUTES
        assert chamadas["fechado"] is True
        assert graph_module._compiled_graph is None

    @pytest.mark.asyncio
    async def test_redis_indisponivel_degrada_para_memory_saver(self, monkeypatch):
        monkeypatch.setattr(settings, "REDIS_URL", "redis://fake:6379")

        @asynccontextmanager
        async def falha(url, ttl=None):
            raise ConnectionError("redis fora do ar")
            yield  # pragma: no cover

        with patch(
            "langgraph.checkpoint.redis.aio.AsyncRedisSaver.from_conn_string",
            side_effect=falha,
        ):
            async with checkpointer_module.checkpointer_lifespan():
                assert isinstance(graph_module.get_compiled_graph().checkpointer, MemorySaver)

    @pytest.mark.parametrize("ttl_minutos, esperado", [(0, None), (-1, None), (60, 60)])
    def test_ttl_config(self, monkeypatch, ttl_minutos, esperado):
        monkeypatch.setattr(settings, "CHECKPOINT_TTL_MINUTES", ttl_minutos)
        cfg = checkpointer_module._ttl_config()
        assert (cfg["default_ttl"] if cfg else None) == esperado
