"""Testes de integração do grafo multiagente com dependências mockadas."""

from app.graph.agent_graph import build_graph
from app.models.cep_model import CepOutput
from app.models.llm_models import PlannerOutput
from app.models.weather_model import WeatherErrorOutput, WeatherOutput


class _FakeStructured:
    """Wrapper simples para simular structured output do modelo."""

    def __init__(self, payload: PlannerOutput):
        self._payload = payload

    def invoke(self, _messages):
        return self._payload


class _FakeModel:
    """Modelo fake com suporte a with_structured_output."""

    def __init__(self, payload: PlannerOutput):
        self._payload = payload

    def with_structured_output(self, _schema):
        return _FakeStructured(self._payload)


def _base_state(message: str) -> dict:
    return {
        "user_message": message,
        "request_id": "test-request",
        "intent": "",
        "plan": "",
        "target_agent": "",
        "needs_tool": False,
        "tool_name": None,
        "cep": None,
        "tool_input": None,
        "tool_result": None,
        "error_message": None,
        "specialist_notes": None,
        "critic_notes": None,
        "agent_path": [],
        "agent_timings": {},
        "response": "",
    }


def test_graph_weather_success(monkeypatch):
    """Fluxo completo weather: planner -> specialist -> tool -> critic -> formatter."""
    planner = PlannerOutput(
        intent="weather",
        target_agent="weather_specialist",
        needs_tool=True,
        tool_name="weather_api",
        cep="22041001",
        plan="Consultar clima a partir do CEP informado.",
    )

    monkeypatch.setattr("app.graph.nodes.get_chat_model", lambda: _FakeModel(planner))
    monkeypatch.setattr(
        "app.graph.nodes.get_info_by_cep",
        lambda _cep: {
            "cep": "22041001",
            "city": "Rio de Janeiro",
            "state": "RJ",
            "latitude": -22.97,
            "longitude": -43.18,
        },
    )
    monkeypatch.setattr(
        "app.graph.nodes.process_weather_request",
        lambda _lat, _lng: WeatherOutput(
            temperature=26.1,
            windspeed=8.0,
            weathercode=1,
            is_day=1,
        ),
    )

    graph = build_graph()
    final_state = graph.invoke(_base_state("Como está o clima no CEP 22041001?"))

    assert final_state["intent"] == "weather"
    assert "clima" in final_state["response"].lower()
    assert "Rio de Janeiro" in final_state["response"]
    assert final_state["error_message"] is None
    assert final_state["agent_path"] == [
        "planner",
        "weather_specialist",
        "tool_executor",
        "critic",
        "formatter",
    ]
    assert all(name in final_state["agent_timings"] for name in final_state["agent_path"])


def test_graph_weather_fallback_to_cep(monkeypatch):
    """Quando weather falha, fluxo devolve fallback com dados de CEP."""
    planner = PlannerOutput(
        intent="weather",
        target_agent="weather_specialist",
        needs_tool=True,
        tool_name="weather_api",
        cep="01001000",
        plan="Consultar clima e usar fallback de CEP se necessário.",
    )

    monkeypatch.setattr("app.graph.nodes.get_chat_model", lambda: _FakeModel(planner))
    monkeypatch.setattr(
        "app.graph.nodes.get_info_by_cep",
        lambda _cep: {
            "cep": "01001000",
            "city": "São Paulo",
            "state": "SP",
            "address_type": "Praça",
            "address_name": "da Sé",
            "address": "Praça da Sé",
            "district": "Sé",
            "ddd": "11",
            "latitude": -23.55,
            "longitude": -46.63,
        },
    )
    monkeypatch.setattr(
        "app.graph.nodes.process_weather_request",
        lambda _lat, _lng: WeatherErrorOutput(message="falha"),
    )
    monkeypatch.setattr(
        "app.graph.nodes.process_address_request",
        lambda _cep: CepOutput(
            cep="01001000",
            address_type="Praça",
            address_name="da Sé",
            address="Praça da Sé",
            district="Sé",
            city="São Paulo",
            state="SP",
            ddd="11",
            lat=-23.55,
            lng=-46.63,
        ),
    )

    graph = build_graph()
    final_state = graph.invoke(_base_state("Como está o clima no CEP 01001000?"))

    assert final_state["intent"] == "weather"
    assert "não consegui obter os dados climáticos" in final_state["response"].lower()
    assert "01001-000" in final_state["response"]
    assert "São Paulo" in final_state["response"]


def test_graph_unknown_goes_direct_to_formatter(monkeypatch):
    """Intent unknown deve ir direto para formatter, sem specialist/tool/critic."""
    planner = PlannerOutput(
        intent="unknown",
        target_agent="formatter",
        needs_tool=False,
        tool_name=None,
        cep=None,
        plan="Responder com orientação de uso.",
    )

    monkeypatch.setattr("app.graph.nodes.get_chat_model", lambda: _FakeModel(planner))

    graph = build_graph()
    final_state = graph.invoke(_base_state("Me conta uma piada"))

    assert final_state["intent"] == "unknown"
    assert "não entendi" in final_state["response"].lower()
    assert final_state["agent_path"] == ["planner", "formatter"]
