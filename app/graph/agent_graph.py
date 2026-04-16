"""
Constrói e compila o grafo LangGraph do agente de chat.

Fluxo:
  START
    ↓
  classify_intent   ← Nó LLM: detecta intent + extrai CEP
    ↓
  [roteamento condicional]
    ├── cep / weather → execute_tool → format_response → END
    └── unknown       → format_response → END
"""

from langgraph.graph import END, START, StateGraph

from app.graph.nodes import classify_intent, execute_tool, format_response
from app.graph.state import AgentState


def _route(state: AgentState) -> str:
    """Decide o próximo nó após a classificação."""
    if state["intent"] in ("cep", "weather"):
        return "execute_tool"
    return "format_response"


def build_graph():
    """Monta e compila o StateGraph."""
    graph = StateGraph(AgentState)

    graph.add_node("classify_intent", classify_intent)
    graph.add_node("execute_tool", execute_tool)
    graph.add_node("format_response", format_response)

    graph.add_edge(START, "classify_intent")
    graph.add_conditional_edges("classify_intent", _route)
    graph.add_edge("execute_tool", "format_response")
    graph.add_edge("format_response", END)

    return graph.compile()


# Instância compilada do grafo para uso global
agent_graph = build_graph()
