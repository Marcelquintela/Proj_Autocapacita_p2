"""Estado compartilhado entre os nós do grafo LangGraph."""

from typing_extensions import TypedDict

from app.models.cep_model import CepErrorOutput, CepOutput
from app.models.weather_model import WeatherErrorOutput, WeatherOutput

# União de todos os payloads possíveis produzidos pelos nós de execução
ToolResult = CepOutput | CepErrorOutput | WeatherOutput | WeatherErrorOutput | None


class AgentState(TypedDict):
    """Estrutura de dados que flui por todos os nós do grafo."""

    # --- Entrada ---
    user_message: str

    # --- Classificação ---
    intent: str
    cep: str | None

    # --- Execução ---
    tool_result: ToolResult
    error_message: str | None

    # --- Saída ---
    response: str
