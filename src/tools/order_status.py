"""Tool transacional para consulta de status de pedidos com isolamento de PII."""

import json
import re
from typing import Any, Dict
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.tools.mock_db import get_mock_pedido


class OrderStatusInput(BaseModel):
    """Parâmetros de entrada para a ferramenta buscar_status_pedido."""

    cpf: str = Field(
        ...,
        description="CPF da revendedora autenticada na sessão para validação de acesso.",
        examples=["52998224725", "529.982.247-25"],
    )
    id_pedido: str = Field(
        ...,
        description="Código alfanumérico identificador do pedido (ex: PED-1001).",
        examples=["PED-1001", "PED-2001"],
    )


def _sanitize_cpf(raw_cpf: str) -> str:
    """Extrai apenas os dígitos numéricos do CPF."""
    return re.sub(r"\D", "", raw_cpf.strip())


def _buscar_status_pedido_core(cpf: str, id_pedido: str) -> str:
    """Lógica determinística de consulta de status de pedido com proteção contra vazamento de PII."""
    cpf_limpo = _sanitize_cpf(cpf)

    if not cpf_limpo:
        return json.dumps(
            {
                "status": "erro",
                "codigo": "CPF_INVALIDO",
                "mensagem": "CPF não fornecido ou inválido para autenticação da consulta.",
            },
            ensure_ascii=False,
        )

    pedido = get_mock_pedido(id_pedido)

    if not pedido:
        return json.dumps(
            {
                "status": "nao_encontrado",
                "id_pedido": id_pedido.strip().upper(),
                "mensagem": f"O pedido '{id_pedido.strip().upper()}' não foi localizado no sistema.",
            },
            ensure_ascii=False,
        )

    # REGRA GLOBAL DE SEGURANÇA 1: Zero Vazamento de PII
    # Bloqueio imediato se o CPF autenticado não for o titular do pedido
    cpf_dono = _sanitize_cpf(pedido["cpf"])
    if cpf_limpo != cpf_dono:
        return json.dumps(
            {
                "status": "erro",
                "codigo": "ACESSO_NEGADO",
                "mensagem": (
                    "Acesso não autorizado: O pedido informado pertence a outra revendedora. "
                    "Por estritas políticas de privacidade e proteção de dados (LGPD), não é permitido "
                    "consultar informações de pedidos vinculados a outro CPF."
                ),
            },
            ensure_ascii=False,
        )

    # Retorno seguro dos dados do pedido pertencente à revendedora
    resultado: Dict[str, Any] = {
        "status": "sucesso",
        "id_pedido": pedido["id_pedido"],
        "status_entrega": pedido["status_entrega"],
        "data_previsao": pedido["data_previsao"],
        "transportadora": pedido["transportadora"],
        "codigo_rastreio": pedido["codigo_rastreio"],
        "itens": pedido["itens"],
        "valor_total": pedido["valor_total"],
        "nota_fiscal": pedido.get("nota_fiscal"),
    }

    if "data_entrega_efetiva" in pedido:
        resultado["data_entrega_efetiva"] = pedido["data_entrega_efetiva"]

    return json.dumps(resultado, ensure_ascii=False)


@tool(
    "buscar_status_pedido",
    args_schema=OrderStatusInput,
    return_direct=False,
)
def buscar_status_pedido(cpf: str, id_pedido: str) -> str:
    """Utilize esta ferramenta APENAS quando a revendedora quiser saber onde está o seu pedido, se já foi faturado ou detalhes de entrega."""
    return _buscar_status_pedido_core(cpf=cpf, id_pedido=id_pedido)
