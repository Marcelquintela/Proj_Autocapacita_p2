"""Schema de saída padronizado do endpoint de chat."""

from typing import Any

from pydantic import BaseModel


class ChatResponse(BaseModel):
    """Resposta padronizada do agente de chat."""

    intent: str
    message: str
    data: Any | None = None
