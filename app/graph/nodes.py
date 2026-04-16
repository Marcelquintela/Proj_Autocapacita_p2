"""
Nós do grafo LangGraph.

Cada função recebe o AgentState atual,
executa sua responsabilidade e retorna apenas os campos que alterou.
"""

import logging

from app.agents.cep_agent import process_address_request
from app.agents.weather_agent import process_weather_request
from app.core.weather_codes import describe_weather
from app.llm.client import get_chat_model
from app.llm.prompts import INTENT_SYSTEM_PROMPT
from app.graph.state import AgentState
from app.models.cep_model import CepOutput
from app.models.llm_models import IntentClassification
from app.models.weather_model import WeatherLocation, WeatherOutput
from app.services.cep_service import get_info_by_cep

logger = logging.getLogger(__name__)


def classify_intent(state: AgentState) -> dict:
    """
    Nó 1: usa o LLM com structured output para classificar
    a intenção do usuário e extrair o CEP, se houver.
    """
    logger.info("[node] classify_intent | message=%s", state["user_message"])

    model = get_chat_model()
    structured = model.with_structured_output(IntentClassification)

    result: IntentClassification = structured.invoke([  # type: ignore[assignment]
        {"role": "system", "content": INTENT_SYSTEM_PROMPT},
        {"role": "user", "content": state["user_message"]},
    ])

    logger.info("[node] classify_intent | intent=%s cep=%s", result.intent, result.cep)

    return {"intent": result.intent, "cep": result.cep}


def execute_tool(state: AgentState) -> dict:
    """
    Nó 2: executa a função determinística correspondente à intenção.
    """
    intent = state["intent"]
    cep = state.get("cep")

    logger.info("[node] execute_tool | intent=%s cep=%s", intent, cep)

    if intent == "cep":
        if not cep:
            return {"tool_result": None}
        result = process_address_request(cep)
        return {"tool_result": result}

    if intent == "weather":
        if not cep:
            return {"tool_result": None}
        cep_data = get_info_by_cep(cep)
        if "error" in cep_data:
            return {"tool_result": None}
        lat = cep_data.get("latitude")
        lng = cep_data.get("longitude")
        if lat is None or lng is None:
            return {"tool_result": None}
        weather = process_weather_request(float(lat), float(lng))
        if isinstance(weather, WeatherOutput):
            weather.location = WeatherLocation(
                city=cep_data.get("city"),
                state=cep_data.get("state"),
            )
        return {"tool_result": weather}

    return {"tool_result": None}


def format_response(state: AgentState) -> dict:
    """
    Nó 3: formata a resposta final de forma amigável e fluida.
    """
    intent = state["intent"]
    result = state.get("tool_result")

    logger.info("[node] format_response | intent=%s", intent)

    if intent == "unknown" or result is None:
        return {"response": (
            "Não entendi sua solicitação. "
            "Você pode me perguntar sobre o endereço de um CEP "
            "ou como está o clima em uma localidade. "
            "Exemplos: 'qual o endereço do CEP 01001000?' ou "
            "'como está o clima no CEP 01001000?'"
        )}

    if isinstance(result, CepOutput):
        parts = []
        if result.address_type and result.address_name:
            parts.append(f"{result.address_type} {result.address_name}")
        elif result.address:
            parts.append(result.address)
        if result.district:
            parts.append(f"bairro {result.district}")
        if result.city and result.state:
            parts.append(f"{result.city} - {result.state}")
        if result.ddd:
            parts.append(f"DDD {result.ddd}")
        location = ", ".join(parts) if parts else "localidade não identificada"
        coords = ""
        if result.lat and result.lng:
            coords = f" Coordenadas: {result.lat:.6f}, {result.lng:.6f}."
        cep_fmt = f"{result.cep[:5]}-{result.cep[5:]}" if len(result.cep) == 8 else result.cep
        return {"response": f"O CEP {cep_fmt} corresponde a: {location}.{coords} (Fonte: AwesomeAPI CEP)"}

    if isinstance(result, WeatherOutput):
        location = ""
        if result.location and result.location.city and result.location.state:
            location = f"Em {result.location.city} - {result.location.state}, "
        elif result.location and result.location.city:
            location = f"Em {result.location.city}, "

        periodo = "durante o dia" if result.is_day else "durante a noite"
        condicao = describe_weather(result.weathercode)
        temp = f"{result.temperature}°C" if result.temperature is not None else "temperatura não disponível"
        vento = f"{result.windspeed} km/h" if result.windspeed is not None else "não disponível"

        return {"response": (
            f"{location}o clima está com {condicao} {periodo}, "
            f"temperatura de {temp} "
            f"e vento de {vento}. "
            f"(Fonte: {result.source})"
        )}

    # Modelos de erro (CepErrorOutput / WeatherErrorOutput)
    msg = getattr(result, "message", str(result))
    return {"response": msg}
