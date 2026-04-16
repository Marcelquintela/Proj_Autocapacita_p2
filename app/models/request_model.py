"""Schema de entrada do endpoint de chat."""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Corpo da requisição POST /chat."""

    message: str
