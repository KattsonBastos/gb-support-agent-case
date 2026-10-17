"""Módulo RAG para catálogo e base de conhecimento."""

from src.rag.retriever import consultar_catalogo, get_or_create_vectorstore

__all__ = ["consultar_catalogo", "get_or_create_vectorstore"]
