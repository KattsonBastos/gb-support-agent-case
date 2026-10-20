"""Configurações globais e variáveis de ambiente da aplicação."""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Configurações centralizadas com suporte a variáveis de ambiente e .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Identificação do Serviço
    APP_NAME: str = "GB Revendedora Support Agent API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Provedor LLM (Google Gemini)
    GOOGLE_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    TEMPERATURE: float = 0.2

    # Circuit Breaker e Limites do Grafo
    CIRCUIT_BREAKER_LIMIT: int = 5

    # Estado das Sessões (Checkpointer LangGraph - ADR-001)
    # Sem REDIS_URL o grafo utiliza MemorySaver (testes/dev local).
    REDIS_URL: Optional[str] = None
    CHECKPOINT_TTL_MINUTES: int = 1440

    # Minimização de PII (pseudonimização do CPF em telemetria)
    PII_HASH_SALT: str = "gb-local-dev-salt"

    # Caminhos de Dados e RAG
    DATA_DIR: Path = BASE_DIR / "data"
    CATALOG_PATH: Path = BASE_DIR / "data" / "catalogo_ciclo_15.md"
    CHROMA_DIR: Path = BASE_DIR / "data" / "chromadb"

    def get_effective_gemini_key(self) -> Optional[str]:
        """Retorna a chave da API do Gemini se configurada via GOOGLE_API_KEY ou GEMINI_API_KEY."""
        return self.GEMINI_API_KEY or self.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")


settings = Settings()
