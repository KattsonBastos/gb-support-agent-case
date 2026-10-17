"""Definição do estado (AgentState) do motor de raciocínio LangGraph."""

import operator
from typing import Annotated, Any, Dict, List, Optional, Sequence
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """Estado do agente orquestrador LangGraph.

    Mantém o histórico contínuo da conversa, contexto de segurança da revendedora
    e controle de loops (Circuit Breaker) para garantir isolamento por sessão.
    """

    # Histórico cumulativo de mensagens (Human, AI, Tool, System)
    messages: Annotated[Sequence[BaseMessage], operator.add]

    # Isolamento de contexto e governança de dados
    session_id: str
    cpf: Optional[str]

    # Armazenamento temporário de saídas brutas das ferramentas (RAG e Pedidos)
    contexto_recuperado: Annotated[List[Dict[str, Any]], operator.add]

    # Contador numérico de execuções de ferramentas para Circuit Breaker
    tentativas_tool: int
