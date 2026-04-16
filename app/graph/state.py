"""Estado compartilhado entre os nós do grafo LangGraph."""

from typing_extensions import NotRequired, TypedDict

from app.models.cep_model import CepErrorOutput, CepOutput
from app.models.weather_model import WeatherErrorOutput, WeatherOutput

# União de todos os payloads possíveis produzidos pelos nós de execução
ToolResult = CepOutput | CepErrorOutput | WeatherOutput | WeatherErrorOutput | None


class AgentState(TypedDict):
    """Estrutura de dados que flui por todos os nós do grafo."""

    # --- Entrada ---
    user_message: str
    request_id: NotRequired[str]

    # --- Planejamento (Planner Agent) ---
    intent: str
    plan: str
    target_agent: str
    needs_tool: bool
    tool_name: str | None
    cep: str | None

    # --- Execução (Specialist + Tool Executor) ---
    tool_input: dict | None
    tool_result: ToolResult
    error_message: str | None
    specialist_notes: NotRequired[str | None]

    # --- Crítica (Critic Agent) ---
    critic_notes: str | None

    # --- Observabilidade ---
    agent_path: NotRequired[list[str]]
    agent_timings: NotRequired[dict[str, float]]

    # --- Saída ---
    response: str
