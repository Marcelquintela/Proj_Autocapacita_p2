"""
Rota do agente de chat: recebe texto do usuário e retorna resposta estruturada.
"""

import logging

from fastapi import APIRouter, HTTPException

from app.models.request_model import ChatRequest
from app.models.response_model import ChatResponse
from app.services.agent_service import run_agent

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Endpoint principal do agente.

    Recebe uma mensagem de texto, classifica a intenção via LLM,
    executa a integração correspondente (CEP ou clima) e retorna
    uma resposta estruturada.
    """
    try:
        return run_agent(request)
    except Exception as exc:
        logger.exception("[route] /chat error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
