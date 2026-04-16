"""
Testes unitários básicos para os nós do grafo.

Testes para validação de lógica pura (sem chamadas ao LLM).
Testes com mocks para nós que dependem de LLM.
"""

import pytest
from unittest.mock import Mock, patch

from app.graph.nodes import (
    cep_specialist_node,
    weather_specialist_node,
    execute_tool,
    critic_node,
    format_response,
    handle_error,
)
from app.graph.state import AgentState
from app.models.cep_model import CepOutput, CepErrorOutput
from app.models.weather_model import WeatherOutput, WeatherLocation


# ============================================================================
# TESTES: CEP SPECIALIST NODE (sem LLM)
# ============================================================================

def test_cep_specialist_node_validates_valid_cep():
    """
    Teste: CEP Specialist deve validar e preparar CEP válido para execução.
    """
    state = AgentState(
        user_message="Qual é o endereço do CEP 01001000?",
        intent="cep",
        plan="Consultar CEP",
        target_agent="cep_specialist",
        needs_tool=True,
        tool_name="cep_api",
        cep="01001000",
        tool_input=None,
        tool_result=None,
        error_message=None,
        critic_notes=None,
        response="",
    )

    result = cep_specialist_node(state)

    assert result["tool_input"] == {"cep": "01001000"}
    assert result["error_message"] is None
    assert "validado" in result["specialist_notes"].lower()


def test_cep_specialist_node_rejects_missing_cep():
    """
    Teste: CEP Specialist deve rejeitar quando CEP está ausente.
    """
    state = AgentState(
        user_message="Qual é o endereço?",
        intent="cep",
        plan="Consultar CEP",
        target_agent="cep_specialist",
        needs_tool=True,
        tool_name="cep_api",
        cep=None,
        tool_input=None,
        tool_result=None,
        error_message=None,
        critic_notes=None,
        response="",
    )

    result = cep_specialist_node(state)

    assert result["tool_input"] is None
    assert "não fornecido" in result["error_message"].lower()


def test_cep_specialist_node_rejects_invalid_cep_format():
    """
    Teste: CEP Specialist deve rejeitar CEP com formato inválido (< 8 dígitos).
    """
    state = AgentState(
        user_message="Qual é o endereço do CEP 1234?",
        intent="cep",
        plan="Consultar CEP",
        target_agent="cep_specialist",
        needs_tool=True,
        tool_name="cep_api",
        cep="1234",
        tool_input=None,
        tool_result=None,
        error_message=None,
        critic_notes=None,
        response="",
    )

    result = cep_specialist_node(state)

    assert result["tool_input"] is None
    assert "inválido" in result["error_message"].lower()


def test_cep_specialist_node_rejects_non_numeric_cep():
    """
    Teste: CEP Specialist deve rejeitar CEP com caracteres não numéricos.
    """
    state = AgentState(
        user_message="Qual é o endereço do CEP ABC01000?",
        intent="cep",
        plan="Consultar CEP",
        target_agent="cep_specialist",
        needs_tool=True,
        tool_name="cep_api",
        cep="ABC01000",
        tool_input=None,
        tool_result=None,
        error_message=None,
        critic_notes=None,
        response="",
    )

    result = cep_specialist_node(state)

    assert result["tool_input"] is None
    assert "inválido" in result["error_message"].lower()


# ============================================================================
# TESTES: PLANNER NODE
# ============================================================================

def test_planner_node_classifies_cep_intent():
    """
    Teste: Planner deve classificar intenção como 'cep'
    quando o usuário pergunta sobre um CEP.
    """
    state = AgentState(
        user_message="Qual é o endereço do CEP 01001000?",
        intent="",
        plan="",
        target_agent="",
        needs_tool=False,
        tool_name=None,
        cep=None,
        tool_input=None,
        tool_result=None,
        error_message=None,
        critic_notes=None,
        response="",
    )

    result = planner_node(state)

    assert result["intent"] == "cep"
    assert result["target_agent"] == "cep_specialist"
    assert result["needs_tool"] is True
    assert result["tool_name"] == "cep_api"
    assert result["cep"] == "01001000"
    assert result["error_message"] is None


def test_planner_node_classifies_weather_intent():
    """
    Teste: Planner deve classificar intenção como 'weather'
    quando o usuário pergunta sobre o clima.
    """
    state = AgentState(
        user_message="Como está o clima no CEP 22041001?",
        intent="",
        plan="",
        target_agent="",
        needs_tool=False,
        tool_name=None,
        cep=None,
        tool_input=None,
        tool_result=None,
        error_message=None,
        critic_notes=None,
        response="",
    )

    result = planner_node(state)

    assert result["intent"] == "weather"
    assert result["target_agent"] == "weather_specialist"
    assert result["needs_tool"] is True
    assert result["tool_name"] == "weather_api"


def test_planner_node_classifies_unknown_intent():
    """
    Teste: Planner deve classificar como 'unknown'
    quando a intenção não é clara.
    """
    state = AgentState(
        user_message="Olá, como você está?",
        intent="",
        plan="",
        target_agent="",
        needs_tool=False,
        tool_name=None,
        cep=None,
        tool_input=None,
        tool_result=None,
        error_message=None,
        critic_notes=None,
        response="",
    )

    result = planner_node(state)

    assert result["intent"] == "unknown"
    assert result["target_agent"] == "formatter"
    assert result["needs_tool"] is False


# ============================================================================
# TESTES: CEP SPECIALIST NODE
# ============================================================================

def test_cep_specialist_node_validates_cep():
    """
    Teste: CEP Specialist deve validar e preparar CEP para execução.
    """
    state = AgentState(
        user_message="Qual é o endereço do CEP 01001000?",
        intent="cep",
        plan="Consultar CEP",
        target_agent="cep_specialist",
        needs_tool=True,
        tool_name="cep_api",
        cep="01001000",
        tool_input=None,
        tool_result=None,
        error_message=None,
        critic_notes=None,
        response="",
    )

    result = cep_specialist_node(state)

    assert result["tool_input"] == {"cep": "01001000"}
    assert result["error_message"] is None
    assert "validado" in result["specialist_notes"].lower()


def test_cep_specialist_node_rejects_missing_cep():
    """
    Teste: CEP Specialist deve rejeitar quando CEP está ausente.
    """
    state = AgentState(
        user_message="Qual é o endereço?",
        intent="cep",
        plan="Consultar CEP",
        target_agent="cep_specialist",
        needs_tool=True,
        tool_name="cep_api",
        cep=None,
        tool_input=None,
        tool_result=None,
        error_message=None,
        critic_notes=None,
        response="",
    )

    result = cep_specialist_node(state)

    assert result["tool_input"] is None
    assert "não fornecido" in result["error_message"].lower()


def test_cep_specialist_node_rejects_invalid_cep():
    """
    Teste: CEP Specialist deve rejeitar CEP com formato inválido.
    """
    state = AgentState(
        user_message="Qual é o endereço do CEP 1234?",
        intent="cep",
        plan="Consultar CEP",
        target_agent="cep_specialist",
        needs_tool=True,
        tool_name="cep_api",
        cep="1234",
        tool_input=None,
        tool_result=None,
        error_message=None,
        critic_notes=None,
        response="",
    )

    result = cep_specialist_node(state)

    assert result["tool_input"] is None
    assert "inválido" in result["error_message"].lower()


# ============================================================================
# TESTES: WEATHER SPECIALIST NODE
# ============================================================================

def test_weather_specialist_node_validates_cep():
    """
    Teste: Weather Specialist deve validar e preparar CEP para execução.
    """
    state = AgentState(
        user_message="Como está o clima no CEP 22041001?",
        intent="weather",
        plan="Consultar clima",
        target_agent="weather_specialist",
        needs_tool=True,
        tool_name="weather_api",
        cep="22041001",
        tool_input=None,
        tool_result=None,
        error_message=None,
        critic_notes=None,
        response="",
    )

    result = weather_specialist_node(state)

    assert result["tool_input"] == {"cep": "22041001"}
    assert result["error_message"] is None
    assert "validado" in result["specialist_notes"].lower()


def test_weather_specialist_node_rejects_missing_cep():
    """
    Teste: Weather Specialist deve rejeitar quando CEP está ausente.
    """
    state = AgentState(
        user_message="Como está o clima?",
        intent="weather",
        plan="Consultar clima",
        target_agent="weather_specialist",
        needs_tool=True,
        tool_name="weather_api",
        cep=None,
        tool_input=None,
        tool_result=None,
        error_message=None,
        critic_notes=None,
        response="",
    )

    result = weather_specialist_node(state)

    assert result["tool_input"] is None
    assert "não fornecido" in result["error_message"].lower()


# ============================================================================
# TESTES: CRITIC NODE
# ============================================================================

def test_critic_node_evaluates_cep_result():
    """
    Teste: Critic deve avaliar resultado de CEP como coerente.
    """
    cep_output = CepOutput(
        cep="01001000",
        address="Avenida Paulista",
        address_name="Avenida Paulista",
        address_type="Avenida",
        district="Bela Vista",
        city="São Paulo",
        state="SP",
        ddd="11",
        lat=-23.561414,
        lng=-46.656139,
    )

    state = AgentState(
        user_message="Qual é o endereço do CEP 01001000?",
        intent="cep",
        plan="Consultar CEP",
        target_agent="cep_specialist",
        needs_tool=True,
        tool_name="cep_api",
        cep="01001000",
        tool_input={"cep": "01001000"},
        tool_result=cep_output,
        error_message=None,
        critic_notes=None,
        response="",
    )

    result = critic_node(state)

    assert "sucesso" in result["critic_notes"].lower() or "obtido" in result["critic_notes"].lower()


def test_critic_node_evaluates_error_result():
    """
    Teste: Critic deve avaliar erro técnico.
    """
    state = AgentState(
        user_message="Qual é o endereço do CEP 01001000?",
        intent="cep",
        plan="Consultar CEP",
        target_agent="cep_specialist",
        needs_tool=True,
        tool_name="cep_api",
        cep="01001000",
        tool_input={"cep": "01001000"},
        tool_result=None,
        error_message="API indisponível",
        critic_notes=None,
        response="",
    )

    result = critic_node(state)

    assert "erro" in result["critic_notes"].lower()


# ============================================================================
# TESTES: EXECUTE TOOL
# ============================================================================

def test_execute_tool_skips_when_no_tool_needed():
    """
    Teste: Execute Tool deve pular quando não há ferramenta necessária.
    """
    state = AgentState(
        user_message="Olá",
        intent="unknown",
        plan="Sem ação",
        target_agent="formatter",
        needs_tool=False,
        tool_name=None,
        cep=None,
        tool_input=None,
        tool_result=None,
        error_message=None,
        critic_notes=None,
        response="",
    )

    result = execute_tool(state)

    assert result["tool_result"] is None
    assert result["error_message"] is None


# ============================================================================
# TESTES: FORMAT RESPONSE
# ============================================================================

def test_format_response_handles_unknown_intent():
    """
    Teste: Formatter deve gerar mensagem padrão para intent desconhecido.
    """
    state = AgentState(
        user_message="Olá",
        intent="unknown",
        plan="Sem ação",
        target_agent="formatter",
        needs_tool=False,
        tool_name=None,
        cep=None,
        tool_input=None,
        tool_result=None,
        error_message=None,
        critic_notes=None,
        response="",
    )

    result = format_response(state)

    assert "não entendi" in result["response"].lower()


def test_format_response_handles_error():
    """
    Teste: Formatter deve retornar mensagem de erro quando há error_message.
    """
    state = AgentState(
        user_message="Qual é o endereço do CEP 01001000?",
        intent="cep",
        plan="Consultar CEP",
        target_agent="cep_specialist",
        needs_tool=True,
        tool_name="cep_api",
        cep="01001000",
        tool_input={"cep": "01001000"},
        tool_result=None,
        error_message="Nenhum CEP foi encontrado na sua mensagem. Por favor, informe um CEP válido.",
        critic_notes="Erro técnico",
        response="",
    )

    result = format_response(state)

    assert result["response"] == "Nenhum CEP foi encontrado na sua mensagem. Por favor, informe um CEP válido."


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
