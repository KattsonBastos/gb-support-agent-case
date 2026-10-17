"""Testes unitários para o cliente e gerador SSE da interface Streamlit."""

from unittest.mock import MagicMock, patch
import requests
from frontend.app import stream_chat_response


class TestStreamChatResponse:
    """Validações da função de streaming SSE do frontend."""

    @patch("requests.post")
    def test_stream_chat_response_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            'data: {"chunk": "Olá,"}',
            "",
            'data: {"chunk": " consultora"}',
            "",
            'data: {"chunk": " Boticário!"}',
        ]
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_post.return_value = mock_response

        chunks = list(
            stream_chat_response(
                api_url="http://localhost:8000/api/v1/chat/stream",
                session_id="test-session-frontend",
                message="Oi",
                cpf="529.982.247-25",
            )
        )

        assert chunks == ["Olá,", " consultora", " Boticário!"]
        mock_post.assert_called_once_with(
            "http://localhost:8000/api/v1/chat/stream",
            json={
                "session_id": "test-session-frontend",
                "message": "Oi",
                "cpf": "529.982.247-25",
            },
            stream=True,
            timeout=60,
        )

    @patch("requests.post")
    def test_stream_chat_response_connection_error(self, mock_post):
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        chunks = list(
            stream_chat_response(
                api_url="http://localhost:8000/api/v1/chat/stream",
                session_id="test-session-frontend",
                message="Oi",
                cpf="529.982.247-25",
            )
        )

        result_text = "".join(chunks)
        assert "Erro de Conexão com o Backend" in result_text
        assert "uvicorn src.main:app" in result_text

    @patch("requests.post")
    def test_stream_chat_response_validation_error_422(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.json.return_value = {"detail": [{"loc": ["body", "cpf"], "msg": "CPF inválido"}]}
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_post.return_value = mock_response

        chunks = list(
            stream_chat_response(
                api_url="http://localhost:8000/api/v1/chat/stream",
                session_id="test-session-frontend",
                message="Oi",
                cpf="000.000.000-00",
            )
        )

        result_text = "".join(chunks)
        assert "Erro de validação (422)" in result_text
        assert "CPF inválido" in result_text
