"""Banco de dados mockado para pedidos da Revendedora do Grupo Boticário.

Simula a integração com o ERP/Logística do GB com isolamento rigoroso por CPF.
"""

from typing import Any, Dict, Optional

# Base simulada de pedidos indexada por id_pedido
MOCK_PEDIDOS_DB: Dict[str, Dict[str, Any]] = {
    "PED-1001": {
        "id_pedido": "PED-1001",
        "cpf": "52998224725",
        "revendedora_nome": "Juliana Silveira",
        "status_entrega": "Em transporte",
        "data_previsao": "20/10/2026",
        "transportadora": "Jadlog Logística",
        "codigo_rastreio": "JAD123456789BR",
        "itens": [
            {"codigo": "BOT-1001", "nome": "Malbec Colônia 100ml", "qtd": 1, "valor": 159.92},
            {"codigo": "COMBO-LILY-15", "nome": "Combo Lily Especial Ciclo 15", "qtd": 1, "valor": 199.00},
        ],
        "valor_total": 358.92,
        "nota_fiscal": "001.982.341-SÉRIE 2",
    },
    "PED-1002": {
        "id_pedido": "PED-1002",
        "cpf": "52998224725",
        "revendedora_nome": "Juliana Silveira",
        "status_entrega": "Entregue",
        "data_previsao": "12/10/2026",
        "data_entrega_efetiva": "11/10/2026 14:32",
        "transportadora": "Total Express",
        "codigo_rastreio": "TEX987654321BR",
        "itens": [
            {"codigo": "MB-5010", "nome": "Make B. Batom Matte Velvet", "qtd": 2, "valor": 109.80},
        ],
        "valor_total": 109.80,
        "nota_fiscal": "001.975.120-SÉRIE 2",
    },
    "PED-2001": {
        "id_pedido": "PED-2001",
        "cpf": "14183884784",
        "revendedora_nome": "Camila Guimarães",
        "status_entrega": "Faturado - Aguardando Coleta",
        "data_previsao": "25/10/2026",
        "transportadora": "Correios Sedex",
        "codigo_rastreio": "BR456789123AA",
        "itens": [
            {"codigo": "EUD-4001", "nome": "Eudora Siàge Shampoo Nutri Rosé", "qtd": 2, "valor": 89.80},
            {"codigo": "EUD-4002", "nome": "Eudora Siàge Condicionador Nutri Rosé", "qtd": 2, "valor": 99.80},
            {"codigo": "EUD-4003", "nome": "Máscara Eudora Siàge Nutri Rosé", "qtd": 1, "valor": 48.93},
        ],
        "valor_total": 238.53,
        "nota_fiscal": "002.114.789-SÉRIE 1",
    },
    "PED-2002": {
        "id_pedido": "PED-2002",
        "cpf": "14183884784",
        "revendedora_nome": "Camila Guimarães",
        "status_entrega": "Em separação no centro de distribuição",
        "data_previsao": "28/10/2026",
        "transportadora": "Azul Cargo Express",
        "codigo_rastreio": "AZU333222111BR",
        "itens": [
            {"codigo": "SPA-7001", "nome": "Nativa SPA Loção Ameixa 400ml + Refil", "qtd": 1, "valor": 109.85},
        ],
        "valor_total": 109.85,
        "nota_fiscal": "Pendente de emissão",
    },
}


def get_mock_pedido(id_pedido: str) -> Optional[Dict[str, Any]]:
    """Recupera um pedido da base mockada pelo seu ID (case-insensitive)."""
    return MOCK_PEDIDOS_DB.get(id_pedido.strip().upper())
