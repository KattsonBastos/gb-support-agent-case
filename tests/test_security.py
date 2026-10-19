"""Testes de minimização de PII: pseudonimização do CPF e erros de streaming sem vazamento."""

import json

import pytest
from fastapi.testclient import TestClient

from src.api import routes
from src.core.security import pseudonimizar_cpf
from src.main import app

CPF_JULIANA = "52998224725"
CPF_CAMILA = "14183884784"


class TestPseudonimizacaoCpf:
    """Garante que o CPF nunca é enviado em texto claro para a telemetria."""

    @pytest.mark.parametrize("cpf", [CPF_JULIANA, CPF_CAMILA])
    def test_nao_contem_cpf_em_claro(self, cpf: str):
        pseudonimo = pseudonimizar_cpf(cpf)
        assert pseudonimo is not None
        assert cpf not in pseudonimo
        assert pseudonimo.startswith("rev-")

    def test_deterministico_por_revendedora(self):
        assert pseudonimizar_cpf(CPF_JULIANA) == pseudonimizar_cpf(CPF_JULIANA)

    def test_revendedoras_diferentes_geram_ids_diferentes(self):
        assert pseudonimizar_cpf(CPF_JULIANA) != pseudonimizar_cpf(CPF_CAMILA)

    @pytest.mark.parametrize("cpf", [None, ""])
    def test_cpf_ausente_retorna_none(self, cpf):
        assert pseudonimizar_cpf(cpf) is None


class _GrafoComFalha:
    """Grafo falso que falha com uma mensagem contendo dado sensível."""

    async def astream_events(self, *args, **kwargs):
        raise RuntimeError(f"falha ao consultar pedido do CPF {CPF_JULIANA}")
        yield  # pragma: no cover - torna a função um gerador assíncrono


class TestErroDeStreamingSemVazamento:
    """Erros durante o stream não podem expor detalhes internos nem PII."""

    def test_chunk_de_erro_generico(self, monkeypatch, caplog):
        monkeypatch.setattr(routes, "get_compiled_graph", lambda: _GrafoComFalha())
        client = TestClient(app)

        payload = {"session_id": "revendedora-erro-1", "message": "Onde está meu pedido?"}
        response = client.post("/api/v1/chat/stream", json=payload)

        assert response.status_code == 200
        assert CPF_JULIANA not in response.text

        linha = next(l for l in response.text.splitlines() if l.startswith("data: "))
        dados = json.loads(linha[len("data: "):])
        assert dados["code"] == "STREAM_ERROR"
        assert CPF_JULIANA not in caplog.text
