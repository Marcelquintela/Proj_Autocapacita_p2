"""Schema de saída padronizado do endpoint de chat."""

from typing import Annotated

from pydantic import BaseModel, Field

from app.models.cep_model import CepErrorOutput, CepOutput
from app.models.weather_model import WeatherErrorOutput, WeatherOutput

# União tipada de todos os payloads possíveis no campo data
ChatData = CepOutput | CepErrorOutput | WeatherOutput | WeatherErrorOutput | None


class ChatResponse(BaseModel):
    """Resposta padronizada do agente de chat."""

    success: bool = Field(
        description="Indica se a solicitação foi processada com sucesso."
    )
    intent: str = Field(
        description="Intenção classificada pelo agente: 'cep', 'weather' ou 'unknown'."
    )
    message: str = Field(
        description="Mensagem textual formatada para exibição ao usuário."
    )
    data: Annotated[ChatData, Field(
        default=None,
        description=(
            "Payload estruturado do resultado: CepOutput, CepErrorOutput, "
            "WeatherOutput ou WeatherErrorOutput. Null quando não houver dado."
        ),
    )] = None
    agent_path: list[str] | None = Field(
        default=None,
        description="Caminho percorrido pelos agentes no grafo (para debug). Ex: ['planner', 'weather_specialist', 'tool', 'critic', 'formatter']."
    )
