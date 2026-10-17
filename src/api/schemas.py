"""Schemas Pydantic para validação de contratos da API de Suporte à Revendedora GB."""

import json
import re
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


def _clean_and_validate_cpf(v: Optional[str]) -> Optional[str]:
    """Valida e normaliza o CPF da revendedora.

    Aplica as regras oficiais da Receita Federal:
    - Remoção de caracteres não-numéricos
    - Verificação de 11 dígitos
    - Bloqueio de sequências repetidas (ex: 111.111.111-11)
    - Verificação matemática dos dois dígitos verificadores (DV1 e DV2)
    """
    if v is None:
        return None

    # Remove qualquer caractere que não seja dígito numérico
    cpf = re.sub(r"\D", "", v.strip())

    if len(cpf) != 11:
        raise ValueError("CPF deve conter exatamente 11 dígitos numéricos.")

    # Rejeita CPFs com todos os dígitos iguais (ex: 00000000000, 11111111111)
    if cpf == cpf[0] * 11:
        raise ValueError("CPF inválido: sequência com dígitos repetidos não permitida.")

    # Cálculo do primeiro dígito verificador
    soma_dv1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto_dv1 = (soma_dv1 * 10) % 11
    digito_1 = 0 if resto_dv1 == 10 else resto_dv1
    if digito_1 != int(cpf[9]):
        raise ValueError("CPF inválido: primeiro dígito verificador incorreto.")

    # Cálculo do segundo dígito verificador
    soma_dv2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto_dv2 = (soma_dv2 * 10) % 11
    digito_2 = 0 if resto_dv2 == 10 else resto_dv2
    if digito_2 != int(cpf[10]):
        raise ValueError("CPF inválido: segundo dígito verificador incorreto.")

    return cpf


class ChatRequest(BaseModel):
    """Payload de entrada para o endpoint de chat em streaming."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(
        ...,
        description="Identificador único da revendedora para manter contexto e isolamento de sessão.",
        examples=["revendedora-123", "a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Mensagem ou intenção enviada pela revendedora.",
        examples=["Onde está meu pedido 12345?", "Quais são as promoções do ciclo 15?"],
    )
    cpf: Optional[str] = Field(
        default=None,
        description="Opcional. CPF da revendedora ativa na sessão para uso e validação estrita nas Tools transacionais.",
        examples=["52998224725", "529.982.247-25"],
    )

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("session_id não pode ser vazio.")
        if len(cleaned) < 3:
            raise ValueError("session_id deve ter no mínimo 3 caracteres.")
        return cleaned

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("message não pode ser vazia.")
        return cleaned

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: Optional[str]) -> Optional[str]:
        return _clean_and_validate_cpf(v)


class ChatStreamChunk(BaseModel):
    """Estrutura de cada chunk transmitido via SSE."""

    chunk: str = Field(..., description="Fragmento de texto gerado para streaming.")

    def to_sse(self) -> str:
        """Formata o chunk no padrão estrito de Server-Sent Events (SSE)."""
        payload = json.dumps({"chunk": self.chunk}, ensure_ascii=False)
        return f"data: {payload}\n\n"


class ErrorResponse(BaseModel):
    """Modelo padrão para erros na API."""

    detail: str = Field(..., description="Descrição legível do erro.")
    code: Optional[str] = Field(default=None, description="Código identificador do erro.")
