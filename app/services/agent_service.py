"""
Serviço de agente: ponte entre a rota FastAPI e o grafo LangGraph.
"""

import logging
from uuid import uuid4

from app.graph.agent_graph import agent_graph
from app.graph.state import AgentState
from app.models.request_model import ChatRequest
from app.models.response_model import ChatResponse

logger = logging.getLogger(__name__)

_FALLBACK_RESPONSE = (
    "Ocorreu um erro interno ao processar sua solicitação."
    "Tente novamente em instantes."
)


def _build_initial_state(message: str, request_id: str) -> AgentState:
    """Monta o estado inicial tipado para o grafo."""
    return AgentState(
        user_message=message,
        request_id=request_id,
        # Planejamento
        intent="",
        plan="",
        target_agent="",
        needs_tool=False,
        tool_name=None,
        cep=None,
        # Execução
        tool_input=None,
        tool_result=None,
        error_message=None,
        # Crítica
        critic_notes=None,
        # Observabilidade
        agent_path=[],
        agent_timings={},
        # Saída
        response="",
    )


def run_agent(request: ChatRequest) -> ChatResponse:
    """
    Executa o grafo LangGraph com a mensagem do usuário
    e retorna uma resposta padronizada.
    
    Inclui caminho dos agentes (agent_path) para debug.
    """
    request_id = str(uuid4())
    logger.info("[service] run_agent | request_id=%s message=%s", request_id, request.message)

    try:
        final_state = agent_graph.invoke(_build_initial_state(request.message, request_id))
    except Exception:
        logger.exception("[service] run_agent | request_id=%s graph execution failed | message=%s", request_id, request.message)
        return ChatResponse(
            success=False,
            intent="unknown",
            message=_FALLBACK_RESPONSE,
            data=None,
            agent_path=None,
        )

    intent = final_state.get("intent", "unknown")
    has_error = bool(final_state.get("error_message"))
    message = final_state.get("response") or _FALLBACK_RESPONSE
    tool_result = final_state.get("tool_result")
    critic_notes = final_state.get("critic_notes", "")
    plan = final_state.get("plan", "")
    target_agent = final_state.get("target_agent", "")
    agent_timings = final_state.get("agent_timings", {})

    # Monta caminho de agentes para debug (opcional)
    agent_path = final_state.get("agent_path") or [
        "planner",
        target_agent if target_agent != "formatter" else None,
        "tool_executor" if final_state.get("needs_tool") else None,
        "critic" if final_state.get("needs_tool") else None,
        "formatter",
    ]
    agent_path = [a for a in agent_path if a]

    logger.info(
        "[service] run_agent | request_id=%s intent=%s has_error=%s plan=%s critic_notes=%s agent_path=%s agent_timings=%s",
        request_id,
        intent,
        has_error,
        plan[:50] if plan else "",
        critic_notes[:50] if critic_notes else "",
        agent_path,
        agent_timings,
    )

    return ChatResponse(
        success=not has_error and intent != "unknown",
        intent=intent,
        message=message,
        data=tool_result,
        agent_path=agent_path,
    )
