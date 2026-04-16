"""
Serviço de agente: ponte entre a rota FastAPI e o grafo LangGraph.
"""

import logging

from app.graph.agent_graph import agent_graph
from app.models.request_model import ChatRequest
from app.models.response_model import ChatResponse

logger = logging.getLogger(__name__)


def run_agent(request: ChatRequest) -> ChatResponse:
    """
    Executa o grafo LangGraph com a mensagem do usuário
    e retorna uma resposta padronizada.
    """
    logger.info("[service] run_agent | message=%s", request.message)

    initial_state = {
        "user_message": request.message,
        "intent": "",
        "cep": None,
        "tool_result": None,
        "response": "",
    }

    final_state = agent_graph.invoke(initial_state)

    logger.info("[service] run_agent | intent=%s", final_state["intent"])

    return ChatResponse(
        intent=final_state["intent"],
        message=final_state["response"],
        data=final_state.get("tool_result"),
    )
