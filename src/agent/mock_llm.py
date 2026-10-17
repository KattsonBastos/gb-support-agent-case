"""Mock inteligente do modelo Gemini para testes e execução local sem chave de API."""

import asyncio
import json
import re
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult


class MockGeminiLLM(BaseChatModel):
    """Simulador de ChatModel do Gemini com suporte a Tool Calling e Streaming de Chunks."""

    model_name: str = "gemini-2.5-flash-mock"
    tools: List[Any] = []

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> "MockGeminiLLM":
        new_instance = self.model_copy()
        new_instance.tools = list(tools)
        return new_instance

    @property
    def _llm_type(self) -> str:
        return "mock-gemini-chat-model"

    def _determine_response(self, messages: List[BaseMessage]) -> Dict[str, Any]:
        """Avalia as mensagens para decidir se dispara Tool Call ou resposta final."""
        last_message = messages[-1]

        # Se a última mensagem for retorno de ferramenta (ToolMessage), sintetiza resposta final
        if isinstance(last_message, ToolMessage):
            tool_content = last_message.content
            try:
                data = json.loads(tool_content)
                if data.get("status") == "erro" and data.get("codigo") == "ACESSO_NEGADO":
                    return {
                        "text": (
                            "Por rígidas diretrizes de privacidade e proteção de dados (LGPD), "
                            "não é permitido acessar ou consultar informações de pedidos pertencentes "
                            "a outro CPF. Cada revendedora só tem acesso aos seus próprios pedidos."
                        ),
                        "tool_calls": [],
                    }
                elif data.get("status") == "sucesso":
                    return {
                        "text": (
                            f"Encontrei as informações do seu pedido **{data.get('id_pedido')}**! "
                            f"Status atual: **{data.get('status_entrega')}**. "
                            f"Previsão de entrega: **{data.get('data_previsao')}** via transportadora {data.get('transportadora')}. "
                            f"Código de rastreio: `{data.get('codigo_rastreio')}`."
                        ),
                        "tool_calls": [],
                    }
                elif data.get("status") == "nao_encontrado":
                    return {
                        "text": (
                            f"Não localizei o pedido informado no sistema. Por favor, verifique o código do pedido "
                            "ou entre em contato com sua supervisora de campo."
                        ),
                        "tool_calls": [],
                    }
            except Exception:
                pass

            # Síntese a partir do RAG
            return {
                "text": (
                    "Com base no Catálogo do Ciclo 15, aqui estão os detalhes:\n\n"
                    f"{tool_content}\n\n"
                    "Aproveite as ofertas do ciclo para aumentar seus lucros!"
                ),
                "tool_calls": [],
            }

        # Avaliação de intenção na pergunta da revendedora
        user_text = ""
        for m in reversed(messages):
            if isinstance(m, HumanMessage):
                user_text = m.content
                break

        user_text_lower = user_text.lower()

        # Guardrail 2: Sigilo Comercial (bloqueio de margem de outras consultoras)
        if any(term in user_text_lower for term in ["quanto ganha", "margem de lucro", "lucro de outra", "lucro da maria", "ganho da outra"]):
            return {
                "text": (
                    "Informações comerciais, faturamento individual e margens de lucro de outras consultoras "
                    "são estritamente confidenciais e sigilosas. Cada revendedora possui sua própria política "
                    "de vendas e independência comercial."
                ),
                "tool_calls": [],
            }

        # Intenção 1: Pedidos -> buscar_status_pedido
        order_match = re.search(r"ped[-\s]?\d+", user_text_lower)
        if order_match or any(w in user_text_lower for w in ["pedido", "rastreio", "entrega", "faturado"]):
            id_pedido = order_match.group(0).upper().replace(" ", "") if order_match else "PED-1001"
            # Extrai CPF ou usa fallback da sessão
            cpf_match = re.search(r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}", user_text)
            cpf = cpf_match.group(0) if cpf_match else "52998224725"
            return {
                "text": "",
                "tool_calls": [
                    {
                        "name": "buscar_status_pedido",
                        "args": {"cpf": cpf, "id_pedido": id_pedido},
                        "id": "call_order_123",
                    }
                ],
            }

        # Intenção 2: Catálogo -> consultar_catalogo
        if any(w in user_text_lower for w in ["malbec", "lily", "eudora", "siage", "siàge", "promoção", "promocao", "preço", "preco", "batom", "base", "ciclo"]):
            return {
                "text": "",
                "tool_calls": [
                    {
                        "name": "consultar_catalogo",
                        "args": {"query": user_text},
                        "id": "call_catalog_123",
                    }
                ],
            }

        # Resposta padrão / bate-papo
        return {
            "text": (
                "Olá, revendedora! Como posso ajudar você hoje? Você pode me perguntar sobre "
                "as promoções do Ciclo 15 (Malbec, Lily, Siàge) ou consultar o status de entrega dos seus pedidos."
            ),
            "tool_calls": [],
        }

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        plan = self._determine_response(messages)
        ai_msg = AIMessage(
            content=plan["text"],
            tool_calls=plan["tool_calls"],
        )
        return ChatResult(generations=[ChatGeneration(message=ai_msg)])

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        return self._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        plan = self._determine_response(messages)

        if plan["tool_calls"]:
            # Emite o chunk com tool_calls
            chunk = AIMessageChunk(
                content="",
                tool_call_chunks=[
                    {
                        "name": tc["name"],
                        "args": json.dumps(tc["args"]),
                        "id": tc["id"],
                        "index": i,
                    }
                    for i, tc in enumerate(plan["tool_calls"])
                ],
            )
            yield ChatGenerationChunk(message=chunk)
            return

        # Streaming das palavras do texto final
        words = plan["text"].split(" ")
        for i, word in enumerate(words):
            token = word if i == 0 else " " + word
            chunk = AIMessageChunk(content=token)
            yield ChatGenerationChunk(message=chunk)
            await asyncio.sleep(0.02)
