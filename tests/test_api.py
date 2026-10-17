"""Testes automatizados para validação de Schemas, Rota de Streaming SSE e LangGraph."""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from src.api.schemas import ChatRequest, ChatStreamChunk
from src.main import app
from src.rag.retriever import get_or_create_vectorstore

client = TestClient(app)

# CPF válido de teste gerado pelo algoritmo oficial
VALID_CPF_FORMATTED = "529.982.247-25"
VALID_CPF_CLEAN = "52998224725"


@pytest.fixture(scope="session", autouse=True)
def init_catalog_for_api_tests():
    """Garante que a base vetorial esteja carregada para os testes de streaming."""
    catalog_path = Path(__file__).resolve().parent.parent / "data" / "catalogo_ciclo_15.md"
    get_or_create_vectorstore(catalog_path=catalog_path)


class TestChatRequestSchema:
    """Testes unitários dos validadores do modelo Pydantic ChatRequest."""

    def test_valid_request_without_cpf(self):
        req = ChatRequest(
            session_id="revendedora-sess-001",
            message="Quais as promoções do ciclo?",
        )
        assert req.session_id == "revendedora-sess-001"
        assert req.message == "Quais as promoções do ciclo?"
        assert req.cpf is None

    def test_valid_request_with_formatted_cpf(self):
        req = ChatRequest(
            session_id="revendedora-sess-001",
            message="Onde está meu pedido?",
            cpf=VALID_CPF_FORMATTED,
        )
        assert req.cpf == VALID_CPF_CLEAN

    def test_empty_session_id_fails(self):
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(session_id="   ", message="Olá")
        assert "session_id não pode ser vazio" in str(exc_info.value)

    def test_short_session_id_fails(self):
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(session_id="ab", message="Olá")
        assert "no mínimo 3 caracteres" in str(exc_info.value)

    def test_empty_message_fails(self):
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(session_id="rev-01", message="   ")
        assert "message não pode ser vazia" in str(exc_info.value)

    def test_invalid_cpf_repeated_digits(self):
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(
                session_id="rev-01",
                message="Status do pedido",
                cpf="111.111.111-11",
            )
        assert "dígitos repetidos não permitida" in str(exc_info.value)

    def test_invalid_cpf_wrong_dv(self):
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(
                session_id="rev-01",
                message="Status do pedido",
                cpf="529.982.247-99",
            )
        assert "dígito verificador incorreto" in str(exc_info.value)

    def test_invalid_cpf_length(self):
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(
                session_id="rev-01",
                message="Status do pedido",
                cpf="123456",
            )
        assert "exatamente 11 dígitos" in str(exc_info.value)


class TestChatStreamChunk:
    """Testes de formatação Server-Sent Events (SSE)."""

    def test_chunk_sse_formatting(self):
        chunk = ChatStreamChunk(chunk="Olá")
        sse_str = chunk.to_sse()
        assert sse_str == 'data: {"chunk": "Olá"}\n\n'


class TestChatStreamRoute:
    """Testes de integração do endpoint POST /api/v1/chat/stream e Web Simulator."""

    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_web_simulator_html(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Suporte à Revendedora GB" in response.text

    def test_chat_stream_rag_flow(self):
        """Testa o streaming SSE com acionamento do nó RAG (Catálogo Ciclo 15)."""
        payload = {
            "session_id": "revendedora-test-rag-1",
            "message": "Quais são as promoções do perfume Malbec?",
        }

        response = client.post("/api/v1/chat/stream", json=payload)
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        assert response.headers["cache-control"] == "no-cache"

        body = response.text
        assert "data: {" in body
        # Verifica se pelo menos um chunk de conteúdo foi emitido
        assert "Malbec" in body or "Catálogo" in body

    def test_chat_stream_order_flow(self):
        """Testa o streaming SSE com acionamento da Tool de Pedidos."""
        payload = {
            "session_id": "revendedora-test-order-1",
            "message": "Onde está o meu pedido PED-1001?",
            "cpf": VALID_CPF_FORMATTED,
        }

        response = client.post("/api/v1/chat/stream", json=payload)
        assert response.status_code == 200
        body = response.text
        assert "data: {" in body
        assert "PED-1001" in body or "transporte" in body

    def test_chat_stream_sigilo_comercial_guardrail(self):
        """Testa o Guardrail 2: Sigilo Comercial de margens de lucro de outras consultoras."""
        payload = {
            "session_id": "revendedora-test-sigilo-1",
            "message": "Quanto ganha de lucro a revendedora Maria?",
        }

        response = client.post("/api/v1/chat/stream", json=payload)
        assert response.status_code == 200
        body = response.text
        assert "confidenciais" in body or "sigilosas" in body

    def test_chat_stream_invalid_cpf_returns_422(self):
        payload = {
            "session_id": "revendedora-test-123",
            "message": "Olá",
            "cpf": "000.000.000-00",
        }

        response = client.post("/api/v1/chat/stream", json=payload)
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("cpf" in err["loc"] for err in errors)

    def test_chat_stream_missing_session_id_returns_422(self):
        payload = {
            "message": "Olá",
        }

        response = client.post("/api/v1/chat/stream", json=payload)
        assert response.status_code == 422
