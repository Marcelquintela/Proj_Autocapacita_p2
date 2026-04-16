"""Estado compartilhado entre os nós do grafo LangGraph."""

from typing import Any

from typing_extensions import TypedDict


class AgentState(TypedDict):
    """Estrutura de dados que flui por todos os nós do grafo."""

    # Entrada do usuário
    user_message: str

    # Resultado da classificação de intenção
    intent: str
    cep: str | None

    # Resultado da execução da ferramenta
    tool_result: Any | None

    # Resposta final formatada
    response: str
