"""
Serviço de agente: ponte entre a rota FastAPI e o grafo LangGraph.
"""

import logging

from app.graph.agent_graph import agent_graph
from app.graph.state import AgentState
from app.models.request_model import ChatRequest
from app.models.response_model import ChatResponse

logger = logging.getLogger(__name__)

_FALLBACK_RESPONSE = (
    "Ocorreu um erro interno ao processar sua solicitação."
    "Tente novamente em instantes."
)


def _build_initial_state(message: str) -> AgentState:
    """Monta o estado inicial tipado para o grafo."""
    return AgentState(
        user_message=message,
        intent="",
        cep=None,
        tool_result=None,
        error_message=None,
        response="",
    )


def run_agent(request: ChatRequest) -> ChatResponse:
    """
    Executa o grafo LangGraph com a mensagem do usuário
    e retorna uma resposta padronizada.
    """
    logger.info("[service] run_agent | message=%s", request.message)

    try:
        final_state = agent_graph.invoke(_build_initial_state(request.message))
    except Exception:
        logger.exception("[service] run_agent | graph execution failed | message=%s", request.message)
        return ChatResponse(
            success=False,
            intent="unknown",
            message=_FALLBACK_RESPONSE,
            data=None,
        )

    intent = final_state.get("intent", "unknown")
    has_error = bool(final_state.get("error_message"))
    message = final_state.get("response") or _FALLBACK_RESPONSE
    tool_result = final_state.get("tool_result")

    logger.info("[service] run_agent | intent=%s has_error=%s", intent, has_error)

    return ChatResponse(
        success=not has_error and intent != "unknown",
        intent=intent,
        message=message,
        data=tool_result,
    )
