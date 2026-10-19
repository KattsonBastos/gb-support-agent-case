"""Utilidades de segurança e minimização de PII."""

import hashlib
import hmac
from typing import Optional

from src.core.config import settings


def pseudonimizar_cpf(cpf: Optional[str]) -> Optional[str]:
    """Gera um identificador pseudonimizado e estável para o CPF da revendedora.

    Usa HMAC-SHA256 com o segredo `PII_HASH_SALT`, de modo que o mesmo CPF sempre
    produza o mesmo identificador (permitindo auditoria e agrupamento de traces),
    sem expor o CPF em texto claro em sistemas de telemetria.
    """
    if not cpf:
        return None

    digest = hmac.new(
        key=settings.PII_HASH_SALT.encode("utf-8"),
        msg=cpf.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return f"rev-{digest[:16]}"
