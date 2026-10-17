"""Testes automatizados para conectores de dados: Tool de pedidos e RAG do catálogo."""

import json
from pathlib import Path
import pytest
from src.tools.order_status import buscar_status_pedido, _buscar_status_pedido_core
from src.rag.retriever import consultar_catalogo, get_or_create_vectorstore, _consultar_catalogo_core

CPF_JULIANA_CLEAN = "52998224725"
CPF_JULIANA_FORMATTED = "529.982.247-25"
CPF_CAMILA_CLEAN = "14183884784"


@pytest.fixture(scope="session", autouse=True)
def init_catalog_vectorstore():
    """Garante que a coleção vetorial esteja inicializada para toda a sessão de testes."""
    catalog_file = Path(__file__).resolve().parent.parent / "data" / "catalogo_ciclo_15.md"
    get_or_create_vectorstore(catalog_path=catalog_file)


class TestOrderStatusTool:
    """Validações da ferramenta buscar_status_pedido e regras de segurança de PII."""

    def test_buscar_pedido_proprio_com_sucesso(self):
        resultado_str = _buscar_status_pedido_core(
            cpf=CPF_JULIANA_FORMATTED,
            id_pedido="PED-1001",
        )
        dados = json.loads(resultado_str)

        assert dados["status"] == "sucesso"
        assert dados["id_pedido"] == "PED-1001"
        assert dados["status_entrega"] == "Em transporte"
        assert dados["transportadora"] == "Jadlog Logística"
        assert "Malbec" in str(dados["itens"])

    def test_bloqueio_estrito_acesso_cruzado_pii(self):
        """Regra 1: Zero Vazamento de PII - Juliana tentando acessar pedido da Camila."""
        resultado_str = _buscar_status_pedido_core(
            cpf=CPF_JULIANA_CLEAN,
            id_pedido="PED-2001",  # Pedido pertence à Camila
        )
        dados = json.loads(resultado_str)

        assert dados["status"] == "erro"
        assert dados["codigo"] == "ACESSO_NEGADO"
        assert "não é permitido consultar informações de pedidos vinculados a outro CPF" in dados["mensagem"]

    def test_pedido_nao_encontrado(self):
        resultado_str = _buscar_status_pedido_core(
            cpf=CPF_JULIANA_CLEAN,
            id_pedido="PED-INEXISTENTE-999",
        )
        dados = json.loads(resultado_str)

        assert dados["status"] == "nao_encontrado"
        assert "não foi localizado" in dados["mensagem"]

    def test_cpf_vazio_bloqueado(self):
        resultado_str = _buscar_status_pedido_core(
            cpf="",
            id_pedido="PED-1001",
        )
        dados = json.loads(resultado_str)

        assert dados["status"] == "erro"
        assert dados["codigo"] == "CPF_INVALIDO"

    def test_invocacao_como_langchain_tool(self):
        """Verifica compatibilidade direta com LangGraph/LangChain."""
        resultado = buscar_status_pedido.invoke(
            {"cpf": CPF_CAMILA_CLEAN, "id_pedido": "PED-2001"}
        )
        dados = json.loads(resultado)
        assert dados["status"] == "sucesso"
        assert dados["id_pedido"] == "PED-2001"
        assert dados["status_entrega"] == "Faturado - Aguardando Coleta"


class TestRagCatalogRetriever:
    """Validações do RAG com ChromaDB e catálogo do Ciclo 15."""

    def test_consulta_promocao_malbec(self):
        resultado = _consultar_catalogo_core(query="Qual é a promoção do perfume Malbec?", k=3)
        assert "Malbec" in resultado
        assert "20%" in resultado or "159,92" in resultado

    def test_consulta_combo_lily(self):
        resultado = _consultar_catalogo_core(query="Quanto custa o combo Lily?", k=3)
        assert "Lily" in resultado
        assert "199,00" in resultado or "Combo" in resultado

    def test_consulta_eudora_siage(self):
        resultado = _consultar_catalogo_core(query="promoção shampoo e máscara Siàge", k=3)
        assert "Siàge" in resultado
        assert "Nutri Rosé" in resultado or "30%" in resultado

    def test_consulta_termo_vazio(self):
        resultado = _consultar_catalogo_core(query="   ")
        assert "Nenhum termo de busca fornecido" in resultado

    def test_invocacao_como_langchain_tool(self):
        """Verifica compatibilidade direta com LangGraph/LangChain."""
        resultado = consultar_catalogo.invoke({"query": "Base Make B"})
        assert "Make B." in resultado
        assert "Glycolic TX" in resultado or "Base" in resultado
