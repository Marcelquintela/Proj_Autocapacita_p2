"""
Testes unitários para os nós do grafo (versão simplificada, sem dependências de LLM).
"""

import pytest
from app.graph.nodes import (
    cep_specialist_node,
    weather_specialist_node,
    execute_tool,
    critic_node,
    format_response,
    handle_error,
)
from app.graph.state import AgentState
from app.models.cep_model import CepOutput


# ============================================================================
# TESTES: CEP SPECIALIST NODE (sem LLM)
# ============================================================================

class TestCepSpecialistNode:
    """Testes para validação de CEP."""

    def test_validates_valid_cep(self):
        """CEP válido com 8 dígitos deve ser aceito."""
        state = AgentState(
            user_message="CEP?",
            intent="cep",
            plan="Consultar",
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

    def test_rejects_missing_cep(self):
        """CEP ausente deve ser rejeitado."""
        state = AgentState(
            user_message="Qual é o endereço?",
            intent="cep",
            plan="Consultar",
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
        assert "cep" in result["error_message"].lower()

    def test_rejects_invalid_cep(self):
        """CEP com menos de 8 dígitos deve ser rejeitado."""
        state = AgentState(
            user_message="CEP 1234",
            intent="cep",
            plan="Consultar",
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
# TESTES: WEATHER SPECIALIST NODE (sem LLM)
# ============================================================================

class TestWeatherSpecialistNode:
    """Testes para validação de CEP em consultas de clima."""

    def test_validates_valid_cep(self):
        """CEP válido deve ser aceito."""
        state = AgentState(
            user_message="Clima?",
            intent="weather",
            plan="Consultar",
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

    def test_rejects_missing_cep(self):
        """CEP ausente deve ser rejeitado."""
        state = AgentState(
            user_message="Como está o clima?",
            intent="weather",
            plan="Consultar",
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
        assert "cep" in result["error_message"].lower()


# ============================================================================
# TESTES: CRITIC NODE
# ============================================================================

class TestCriticNode:
    """Testes para análise de resultados."""

    def test_evaluates_cep_output(self):
        """Crítico deve avaliar CepOutput como resultado válido."""
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
            user_message="CEP?",
            intent="cep",
            plan="Consultar",
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

    def test_evaluates_error(self):
        """Crítico deve avaliar erro técnico."""
        state = AgentState(
            user_message="CEP?",
            intent="cep",
            plan="Consultar",
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

class TestExecuteTool:
    """Testes para execução de ferramentas."""

    def test_skips_when_no_tool_needed(self):
        """Deve pular quando não há ferramenta necessária."""
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

    def test_rejects_unknown_tool(self):
        """Deve rejeitar ferramenta desconhecida."""
        state = AgentState(
            user_message="Teste",
            intent="cep",
            plan="Teste",
            target_agent="cep_specialist",
            needs_tool=True,
            tool_name="unknown_api",
            cep="01001000",
            tool_input={"cep": "01001000"},
            tool_result=None,
            error_message=None,
            critic_notes=None,
            response="",
        )
        result = execute_tool(state)
        assert result["tool_result"] is None
        assert "desconhecida" in result["error_message"].lower()


# ============================================================================
# TESTES: FORMAT RESPONSE
# ============================================================================

class TestFormatResponse:
    """Testes para formatação de resposta."""

    def test_handles_unknown_intent(self):
        """Deve gerar mensagem padrão para intent desconhecido."""
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

    def test_handles_error_message(self):
        """Deve retornar mensagem de erro quando present."""
        error = "Nenhum CEP foi encontrado"
        state = AgentState(
            user_message="CEP?",
            intent="cep",
            plan="Consultar",
            target_agent="cep_specialist",
            needs_tool=True,
            tool_name="cep_api",
            cep=None,
            tool_input=None,
            tool_result=None,
            error_message=error,
            critic_notes="Erro",
            response="",
        )
        result = format_response(state)
        assert result["response"] == error

    def test_formats_cep_output(self):
        """Deve formatar CepOutput de forma legível."""
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
            user_message="CEP?",
            intent="cep",
            plan="Consultar",
            target_agent="cep_specialist",
            needs_tool=True,
            tool_name="cep_api",
            cep="01001000",
            tool_input={"cep": "01001000"},
            tool_result=cep_output,
            error_message=None,
            critic_notes="Válido",
            response="",
        )
        result = format_response(state)
        assert "São Paulo" in result["response"]
        assert "SP" in result["response"]


# ============================================================================
# TESTES: HANDLE ERROR
# ============================================================================

class TestHandleError:
    """Testes para tratamento de erros."""

    def test_uses_error_message(self):
        """Deve retornar error_message quando presente."""
        state = AgentState(
            user_message="Teste",
            intent="unknown",
            plan="",
            target_agent="",
            needs_tool=False,
            tool_name=None,
            cep=None,
            tool_input=None,
            tool_result=None,
            error_message="Erro customizado",
            critic_notes=None,
            response="",
        )
        result = handle_error(state)
        assert result["response"] == "Erro customizado"

    def test_uses_fallback(self):
        """Deve usar fallback quando error_message não está presente."""
        state = AgentState(
            user_message="Teste",
            intent="unknown",
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
        result = handle_error(state)
        assert "erro inesperado" in result["response"].lower() or "tente novamente" in result["response"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
