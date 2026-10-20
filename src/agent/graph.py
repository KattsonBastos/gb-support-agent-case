"""Construção do motor cognitivo LangGraph baseado no padrão ReAct com Agentic RAG."""

import json
from typing import Any, Dict, List
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src.agent.mock_llm import MockGeminiLLM
from src.agent.prompts import SYSTEM_PROMPT
from src.agent.state import AgentState
from src.core.config import settings
from src.rag.retriever import consultar_catalogo
from src.tools.order_status import buscar_status_pedido

# Lista de ferramentas disponibilizadas para o modelo
TOOLS = [consultar_catalogo, buscar_status_pedido]

# Erro de negócio retornado quando não há CPF vinculado à sessão (ADR-003)
CPF_SESSAO_AUSENTE_PAYLOAD = json.dumps(
    {
        "status": "erro",
        "codigo": "CPF_SESSAO_AUSENTE",
        "mensagem": (
            "Nenhum CPF está vinculado a esta sessão. Por segurança, a consulta de pedidos "
            "exige o CPF da revendedora configurado na sessão; CPFs informados na conversa não são aceitos."
        ),
    },
    ensure_ascii=False,
)


def get_llm(streaming: bool = True) -> BaseChatModel:
    """Instancia o modelo LLM baseado em Google Gemini ou fallback Mock quando não houver chave."""
    api_key = settings.get_effective_gemini_key()
    if api_key:
        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            temperature=settings.TEMPERATURE,
            google_api_key=api_key,
            streaming=streaming,
        )
    return MockGeminiLLM()


async def orquestrador_node(state: AgentState) -> Dict[str, Any]:
    """Nó Orquestrador Central: injeta Guardrails e avalia intenções via LLM com ferramentas."""
    messages: List[BaseMessage] = list(state.get("messages", []))

    # Injeção do System Prompt com Guardrails no início do histórico
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    llm = get_llm(streaming=True)
    llm_with_tools = llm.bind_tools(TOOLS)

    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response]}


async def executar_rag_node(state: AgentState) -> Dict[str, Any]:
    """Nó Executar_RAG: Realiza busca semântica no catálogo do Ciclo 15."""
    last_message = state["messages"][-1]
    tool_messages: List[ToolMessage] = []
    novos_contextos: List[Dict[str, Any]] = []

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tc in last_message.tool_calls:
            if tc["name"] == "consultar_catalogo":
                query = tc["args"].get("query", "")
                resultado = consultar_catalogo.invoke({"query": query})
                tool_messages.append(
                    ToolMessage(
                        content=resultado,
                        tool_call_id=tc["id"],
                        name="consultar_catalogo",
                    )
                )
                novos_contextos.append(
                    {"tool": "consultar_catalogo", "query": query, "output": resultado}
                )

    return {
        "messages": tool_messages,
        "tentativas_tool": state.get("tentativas_tool", 0) + 1,
        "contexto_recuperado": novos_contextos,
    }


async def executar_api_node(state: AgentState) -> Dict[str, Any]:
    """Nó Executar_API: Invoca a Tool transacional com injeção segura do CPF da sessão."""
    last_message = state["messages"][-1]
    tool_messages: List[ToolMessage] = []
    novos_contextos: List[Dict[str, Any]] = []

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tc in last_message.tool_calls:
            if tc["name"] == "buscar_status_pedido":
                args = dict(tc["args"])

                # DEFESA EM PROFUNDIDADE DETERMINÍSTICA (ADR-003):
                # O CPF da sessão é obrigatório e sempre sobrescreve o CPF gerado pelo LLM.
                # Sem CPF de sessão, a Tool NÃO é invocada (CPF digitado no chat não é aceito).
                cpf_sessao = state.get("cpf")
                if cpf_sessao:
                    args["cpf"] = cpf_sessao
                    resultado = buscar_status_pedido.invoke(args)
                else:
                    args.pop("cpf", None)
                    resultado = CPF_SESSAO_AUSENTE_PAYLOAD

                tool_messages.append(
                    ToolMessage(
                        content=resultado,
                        tool_call_id=tc["id"],
                        name="buscar_status_pedido",
                    )
                )
                novos_contextos.append(
                    {"tool": "buscar_status_pedido", "args": args, "output": resultado}
                )

    return {
        "messages": tool_messages,
        "tentativas_tool": state.get("tentativas_tool", 0) + 1,
        "contexto_recuperado": novos_contextos,
    }


def should_continue_edge(state: AgentState) -> str:
    """Aresta condicional de roteamento para o padrão ReAct.

    Decide se segue para RAG, API ou encerra o fluxo iterativo.
    """
    # Circuit Breaker para evitar loops recursivos
    if state.get("tentativas_tool", 0) >= settings.CIRCUIT_BREAKER_LIMIT:
        return END

    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        primeira_tool = last_message.tool_calls[0].get("name")
        if primeira_tool == "consultar_catalogo":
            return "executar_rag"
        elif primeira_tool == "buscar_status_pedido":
            return "executar_api"
        return "executar_rag"

    return END


def create_agent_graph() -> StateGraph:
    """Monta a estrutura de nós e arestas do StateGraph do LangGraph."""
    workflow = StateGraph(AgentState)

    # Registro de Nós
    workflow.add_node("orquestrador", orquestrador_node)
    workflow.add_node("executar_rag", executar_rag_node)
    workflow.add_node("executar_api", executar_api_node)

    # Definição de Arestas
    workflow.add_edge(START, "orquestrador")
    workflow.add_conditional_edges(
        "orquestrador",
        should_continue_edge,
        {
            "executar_rag": "executar_rag",
            "executar_api": "executar_api",
            END: END,
        },
    )
    workflow.add_edge("executar_rag", "orquestrador")
    workflow.add_edge("executar_api", "orquestrador")

    return workflow


# Instância única compilada com Checkpointer para isolamento de sessão
_compiled_graph = None


def set_compiled_graph(checkpointer: BaseCheckpointSaver) -> None:
    """Compila o grafo com um checkpointer externo (ex.: AsyncRedisSaver) - ADR-001."""
    global _compiled_graph
    _compiled_graph = create_agent_graph().compile(checkpointer=checkpointer)


def reset_compiled_graph() -> None:
    """Descarta o grafo compilado (ex.: no shutdown, ao fechar a conexão com o Redis)."""
    global _compiled_graph
    _compiled_graph = None


def get_compiled_graph():
    """Retorna o grafo compilado; sem checkpointer injetado, usa MemorySaver (fallback local/testes).

    O isolamento por session_id é garantido via `configurable.thread_id`.
    """
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = create_agent_graph().compile(checkpointer=MemorySaver())
    return _compiled_graph
