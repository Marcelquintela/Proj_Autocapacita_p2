"""
Nós do grafo LangGraph.

Cada função recebe o AgentState atual,
executa sua responsabilidade e retorna apenas os campos que alterou.

Arquitetura multiagente:
- planner_node: Classifica intenção e cria plano
- cep_specialist_node: Valida e prepara requisição CEP
- weather_specialist_node: Valida e prepara requisição Weather
- execute_tool: Executa a ferramenta (puro, determinístico)
- critic_node: Avalia resultado e sugere estilo de resposta
- format_response: Formata resposta final usando avaliação do critic
"""

import logging
from time import perf_counter
from typing import Any

from app.agents.cep_agent import process_address_request
from app.agents.weather_agent import process_weather_request
from app.core.weather_codes import describe_weather
from app.llm.client import get_chat_model
from app.llm.prompts import PLANNER_SYSTEM_PROMPT
from app.graph.state import AgentState
from app.models.cep_model import CepErrorOutput, CepOutput
from app.models.llm_models import PlannerOutput
from app.models.weather_model import WeatherErrorOutput, WeatherLocation, WeatherOutput
from app.services.cep_service import get_info_by_cep

logger = logging.getLogger(__name__)


def _build_trace_update(state: AgentState, node_name: str, started_at: float) -> dict[str, Any]:
    """Acumula trilha de execução e tempo por nó no estado."""
    current_path = state.get("agent_path") or []
    current_timings = state.get("agent_timings") or {}
    elapsed_ms = round((perf_counter() - started_at) * 1000, 3)

    return {
        "agent_path": [*current_path, node_name],
        "agent_timings": {
            **current_timings,
            node_name: elapsed_ms,
        },
    }


# ============================================================================
# Nó 1: PLANNER AGENT
# ============================================================================

def planner_node(state: AgentState) -> dict:
    """
    Nó 1: Planner Agent
    - Classifica a intenção
    - Decide qual agente especialista será chamado
    - Estrutura um plano de ação
    - Extrai CEP se presente
    """
    started_at = perf_counter()
    request_id = state.get("request_id", "n/a")
    logger.info("[node] planner_node | request_id=%s message=%s", request_id, state["user_message"])

    try:
        model = get_chat_model()
        structured = model.with_structured_output(PlannerOutput)

        result: PlannerOutput = structured.invoke([  # type: ignore[assignment]
            {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
            {"role": "user", "content": state["user_message"]},
        ])

        logger.info(
            "[node] planner_node | request_id=%s intent=%s target_agent=%s needs_tool=%s",
            request_id,
            result.intent,
            result.target_agent,
            result.needs_tool,
        )

        return {
            "intent": result.intent,
            "plan": result.plan,
            "target_agent": result.target_agent,
            "needs_tool": result.needs_tool,
            "tool_name": result.tool_name,
            "cep": result.cep,
            "error_message": None,
            **_build_trace_update(state, "planner", started_at),
        }
    except Exception:
        logger.exception("[node] planner_node | request_id=%s failed", request_id)
        return {
            "intent": "unknown",
            "plan": "Falha ao classificar a solicitação",
            "target_agent": "formatter",
            "needs_tool": False,
            "tool_name": None,
            "cep": None,
            "error_message": "Não consegui classificar sua solicitação agora. Tente novamente em instantes.",
            **_build_trace_update(state, "planner", started_at),
        }


# ============================================================================
# Nó 2: CEP SPECIALIST AGENT
# ============================================================================

def cep_specialist_node(state: AgentState) -> dict:
    """
    Nó 2: CEP Specialist Agent
    - Valida se o CEP está presente
    - Prepara os parâmetros de entrada (tool_input)
    - Adiciona anotações de domínio
    """
    started_at = perf_counter()
    request_id = state.get("request_id", "n/a")
    logger.info("[node] cep_specialist_node | request_id=%s cep=%s", request_id, state.get("cep"))

    cep = state.get("cep")

    try:
        if not cep:
            return {
                "tool_input": None,
                "specialist_notes": "CEP não fornecido. Não há como prosseguir com a consulta.",
                "error_message": "Nenhum CEP foi encontrado na sua mensagem. Por favor, informe um CEP válido.",
                **_build_trace_update(state, "cep_specialist", started_at),
            }

        # Valida CEP (8 dígitos)
        if not (isinstance(cep, str) and cep.isdigit() and len(cep) == 8):
            return {
                "tool_input": None,
                "specialist_notes": f"CEP inválido: {cep}. Deve conter exatamente 8 dígitos numéricos.",
                "error_message": f"O CEP '{cep}' é inválido. Por favor, informe um CEP válido com 8 dígitos.",
                **_build_trace_update(state, "cep_specialist", started_at),
            }

        # CEP válido
        tool_input = {"cep": cep}
        logger.info("[node] cep_specialist_node | request_id=%s CEP validado e pronto para execução: %s", request_id, cep)

        return {
            "tool_input": tool_input,
            "specialist_notes": f"CEP {cep} validado. Pronto para execução.",
            "error_message": None,
            **_build_trace_update(state, "cep_specialist", started_at),
        }

    except Exception:
        logger.exception("[node] cep_specialist_node | request_id=%s failed", request_id)
        return {
            "tool_input": None,
            "specialist_notes": "Erro ao validar CEP",
            "error_message": "Ocorreu um erro ao validar seu CEP. Tente novamente em instantes.",
            **_build_trace_update(state, "cep_specialist", started_at),
        }


# ============================================================================
# Nó 3: WEATHER SPECIALIST AGENT
# ============================================================================

def weather_specialist_node(state: AgentState) -> dict:
    """
    Nó 3: Weather Specialist Agent
    - Valida se o CEP está presente
    - Prepara os parâmetros de entrada (tool_input)
    - Reconhece que é necessária conversão CEP -> coordenadas -> dados climáticos
    """
    started_at = perf_counter()
    request_id = state.get("request_id", "n/a")
    logger.info("[node] weather_specialist_node | request_id=%s cep=%s", request_id, state.get("cep"))

    cep = state.get("cep")

    try:
        if not cep:
            return {
                "tool_input": None,
                "specialist_notes": "CEP não fornecido. É necessário um CEP para obter dados climáticos.",
                "error_message": "Nenhum CEP foi encontrado na sua mensagem. Por favor, informe um CEP válido.",
                **_build_trace_update(state, "weather_specialist", started_at),
            }

        # Valida CEP (8 dígitos)
        if not (isinstance(cep, str) and cep.isdigit() and len(cep) == 8):
            return {
                "tool_input": None,
                "specialist_notes": f"CEP inválido: {cep}. Deve conter exatamente 8 dígitos numéricos.",
                "error_message": f"O CEP '{cep}' é inválido. Por favor, informe um CEP válido com 8 dígitos.",
                **_build_trace_update(state, "weather_specialist", started_at),
            }

        # CEP válido - prepara para fluxo: CEP -> coordenadas -> clima
        tool_input = {"cep": cep}
        logger.info(
            "[node] weather_specialist_node | request_id=%s CEP validado. Fluxo: CEP -> coordenadas -> clima",
            request_id,
        )

        return {
            "tool_input": tool_input,
            "specialist_notes": f"CEP {cep} validado. Será necessário converter para coordenadas geográficas.",
            "error_message": None,
            **_build_trace_update(state, "weather_specialist", started_at),
        }

    except Exception:
        logger.exception("[node] weather_specialist_node | request_id=%s failed", request_id)
        return {
            "tool_input": None,
            "specialist_notes": "Erro ao validar CEP",
            "error_message": "Ocorreu um erro ao validar seu CEP. Tente novamente em instantes.",
            **_build_trace_update(state, "weather_specialist", started_at),
        }


# ============================================================================
# Nó 4: TOOL EXECUTOR (executivo puro, determinístico)
# ============================================================================

def _execute_cep_tool(cep: str) -> dict:
    """Executa ferramenta: consulta endereço para o CEP fornecido."""
    result = process_address_request(cep)
    return {"tool_result": result, "error_message": None}


def _execute_weather_tool(cep: str) -> dict:
    """Executa ferramenta: consulta clima usando coordenadas do CEP."""
    cep_data = get_info_by_cep(cep)
    if "error" in cep_data:
        return {
            "tool_result": None,
            "error_message": f"Não consegui obter os dados de localização para o CEP {cep}.",
        }
    lat = cep_data.get("latitude")
    lng = cep_data.get("longitude")
    if lat is None or lng is None:
        return {
            "tool_result": None,
            "error_message": "Não foi possível localizar coordenadas geográficas para o CEP informado.",
        }
    weather = process_weather_request(float(lat), float(lng))
    if isinstance(weather, WeatherErrorOutput):
        fallback_address = process_address_request(cep)
        if isinstance(fallback_address, CepOutput):
            return {
                "tool_result": fallback_address,
                "error_message": "Não consegui obter os dados climáticos agora, mas consegui localizar o endereço do CEP informado.",
            }
        return {
            "tool_result": weather,
            "error_message": None,
        }

    if isinstance(weather, WeatherOutput):
        weather.location = WeatherLocation(
            city=cep_data.get("city"),
            state=cep_data.get("state"),
        )
    return {"tool_result": weather, "error_message": None}


def execute_tool(state: AgentState) -> dict:
    """
    Nó 4: Tool Executor (puro, determinístico)
    - Lê tool_name e tool_input do estado
    - Executa a ferramenta correspondente
    - Retorna resultado ou erro
    - NÃO toma decisões de fluxo
    - NÃO raciocina sobre domínio
    """
    started_at = perf_counter()
    request_id = state.get("request_id", "n/a")
    tool_name = state.get("tool_name")
    tool_input = state.get("tool_input")

    logger.info("[node] execute_tool | request_id=%s tool_name=%s tool_input=%s", request_id, tool_name, tool_input)

    # Se não há ferramenta a executar, passa adiante
    if not tool_name or not tool_input:
        logger.info("[node] execute_tool | request_id=%s skipped (no tool needed)", request_id)
        return {
            "tool_result": None,
            "error_message": None,
            **_build_trace_update(state, "tool_executor", started_at),
        }

    try:
        if tool_name == "cep_api":
            cep = tool_input.get("cep")
            if not isinstance(cep, str):
                return {
                    "tool_result": None,
                    "error_message": "Parâmetro inválido para consulta de CEP.",
                    **_build_trace_update(state, "tool_executor", started_at),
                }
            result = _execute_cep_tool(cep)
            return {**result, **_build_trace_update(state, "tool_executor", started_at)}

        if tool_name == "weather_api":
            cep = tool_input.get("cep")
            if not isinstance(cep, str):
                return {
                    "tool_result": None,
                    "error_message": "Parâmetro inválido para consulta de clima.",
                    **_build_trace_update(state, "tool_executor", started_at),
                }
            result = _execute_weather_tool(cep)
            return {**result, **_build_trace_update(state, "tool_executor", started_at)}

        # Tool desconhecida
        return {
            "tool_result": None,
            "error_message": f"Ferramenta desconhecida: {tool_name}",
            **_build_trace_update(state, "tool_executor", started_at),
        }

    except Exception:
        logger.exception("[node] execute_tool | request_id=%s failed", request_id)
        return {
            "tool_result": None,
            "error_message": "Ocorreu um erro ao executar a ferramenta. Tente novamente em instantes.",
            **_build_trace_update(state, "tool_executor", started_at),
        }


# ============================================================================
# Nó 5: CRITIC AGENT
# ============================================================================

def critic_node(state: AgentState) -> dict:
    """
    Nó 5: Critic Agent (Revisor)
    - Analisa o resultado obtido pela ferramenta
    - Verifica coerência e integridade dos dados
    - Identifica falhas semânticas
    - Sugere estilo de resposta para o formatter
    """
    started_at = perf_counter()
    request_id = state.get("request_id", "n/a")
    logger.info("[node] critic_node | request_id=%s tool_result type=%s", request_id, type(state.get("tool_result")))

    tool_result = state.get("tool_result")
    error_message = state.get("error_message")
    intent = state.get("intent")

    try:
        # Se há erro técnico, critic categoriza como erro
        if error_message:
            return {
                "critic_notes": f"Erro técnico detectado: {error_message}",
                **_build_trace_update(state, "critic", started_at),
            }

        # Se não há resultado e era esperado um, é erro
        if tool_result is None and state.get("needs_tool"):
            return {
                "critic_notes": "Nenhum dado foi obtido pela ferramenta, mas era esperado.",
                **_build_trace_update(state, "critic", started_at),
            }

        # Análise por tipo de resultado
        if isinstance(tool_result, CepOutput):
            notes = f"Endereço obtido com sucesso para o CEP fornecido. Dados: {tool_result.city}, {tool_result.state}."
            return {"critic_notes": notes, **_build_trace_update(state, "critic", started_at)}

        if isinstance(tool_result, WeatherOutput):
            temp_str = f"{tool_result.temperature}°C" if tool_result.temperature else "não disponível"
            notes = f"Dados climáticos obtidos com sucesso. Temperatura: {temp_str}."
            return {"critic_notes": notes, **_build_trace_update(state, "critic", started_at)}

        if isinstance(tool_result, (CepErrorOutput, WeatherErrorOutput)):
            return {
                "critic_notes": f"API retornou erro: {tool_result.message}",
                **_build_trace_update(state, "critic", started_at),
            }

        # Intent unknown ou sem tool
        if intent == "unknown" or tool_result is None:
            return {
                "critic_notes": "Nenhuma ferramenta foi executada (intenção desconhecida ou sem necessidade de tool).",
                **_build_trace_update(state, "critic", started_at),
            }

        # Resultado inesperado
        logger.warning("[node] critic_node | unexpected result type: %s", type(tool_result))
        return {
            "critic_notes": f"Tipo de resultado inesperado: {type(tool_result).__name__}",
            **_build_trace_update(state, "critic", started_at),
        }

    except Exception:
        logger.exception("[node] critic_node | request_id=%s failed", request_id)
        return {
            "critic_notes": "Erro ao avaliar resultado.",
            **_build_trace_update(state, "critic", started_at),
        }


# ============================================================================
# Nó 6: RESPONSE FORMATTER
# ============================================================================

def _format_unknown_response() -> str:
    return (
        "Não entendi sua solicitação. "
        "Você pode me perguntar sobre o endereço de um CEP "
        "ou como está o clima em uma localidade. "
        "Exemplos: 'qual o endereço do CEP 01001000?' ou "
        "'como está o clima no CEP 01001000?'"
    )


def _format_cep_response(result: CepOutput) -> str:
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
    return f"O CEP {cep_fmt} corresponde a: {location}.{coords} (Fonte: AwesomeAPI CEP)"


def _format_weather_response(result: WeatherOutput) -> str:
    location = ""
    if result.location and result.location.city and result.location.state:
        location = f"Em {result.location.city} - {result.location.state}, "
    elif result.location and result.location.city:
        location = f"Em {result.location.city}, "

    periodo = "durante o dia" if result.is_day else "durante a noite"
    condicao = describe_weather(result.weathercode)
    temp = f"{result.temperature}°C" if result.temperature is not None else "temperatura não disponível"
    vento = f"{result.windspeed} km/h" if result.windspeed is not None else "não disponível"

    return (
        f"{location}o clima está com {condicao} {periodo}, "
        f"temperatura de {temp} "
        f"e vento de {vento}. "
        f"(Fonte: {result.source})"
    )


def format_response(state: AgentState) -> dict:
    """
    Nó 6: Response Formatter
    - Usa intent, tool_result, critic_notes e error_message
    - Formata resposta amigável e fluida
    - Incorpora avaliação do critic
    """
    started_at = perf_counter()
    request_id = state.get("request_id", "n/a")
    intent = state.get("intent")
    result = state.get("tool_result")
    error_message = state.get("error_message")
    critic_notes = state.get("critic_notes", "")

    logger.info(
        "[node] format_response | request_id=%s intent=%s error=%s critic_notes=%s",
        request_id,
        intent,
        bool(error_message),
        critic_notes[:50] if critic_notes else "",
    )

    # Se houver fallback de weather com CepOutput, monta resposta combinada
    if intent == "weather" and isinstance(result, CepOutput) and error_message:
        return {
            "response": f"{error_message} {_format_cep_response(result)}",
            **_build_trace_update(state, "formatter", started_at),
        }

    # Se há erro, retorna mensagem de erro
    if error_message:
        return {"response": error_message, **_build_trace_update(state, "formatter", started_at)}

    # Intent unknown ou sem resultado
    if intent == "unknown" or result is None:
        return {"response": _format_unknown_response(), **_build_trace_update(state, "formatter", started_at)}

    # Resultados bem-sucedidos
    if isinstance(result, CepOutput):
        return {"response": _format_cep_response(result), **_build_trace_update(state, "formatter", started_at)}

    if isinstance(result, WeatherOutput):
        return {"response": _format_weather_response(result), **_build_trace_update(state, "formatter", started_at)}

    # Erros estruturados das APIs
    if isinstance(result, (CepErrorOutput, WeatherErrorOutput)):
        return {"response": result.message, **_build_trace_update(state, "formatter", started_at)}

    # Fallback para tipo inesperado
    logger.error("[node] format_response | unexpected result type: %s", type(result))
    return {
        "response": "Não foi possível processar a resposta. Tente novamente.",
        **_build_trace_update(state, "formatter", started_at),
    }


# ============================================================================
# Nó de Fallback: HANDLE ERROR
# ============================================================================

def handle_error(state: AgentState) -> dict:
    """
    Nó de fallback para tratar falhas críticas.
    Transforma erro interno em resposta controlada.
    """
    started_at = perf_counter()
    request_id = state.get("request_id", "n/a")
    message = state.get("error_message") or (
        "Ocorreu um erro inesperado ao processar sua solicitação. Tente novamente em instantes."
    )
    logger.warning("[node] handle_error | request_id=%s message=%s", request_id, message)
    return {"response": message, **_build_trace_update(state, "handle_error", started_at)}

