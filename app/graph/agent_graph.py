"""
Constrói e compila o grafo LangGraph do agente de chat.

Fluxo:
  START
    ↓
  classify_intent   ← Nó LLM: detecta intent + extrai CEP
    ↓
  [roteamento condicional]
    ├── erro           → handle_error → END
    ├── cep / weather  → execute_tool
    │                    ↓
    │                  [roteamento condicional]
    │                    ├── erro      → handle_error → END
    │                    └── sucesso   → format_response → END
    └── unknown        → format_response → END
"""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.graph.nodes import classify_intent, execute_tool, format_response, handle_error
from app.graph.state import AgentState


def route_after_classification(state: AgentState) -> str:
    """Decide o próximo nó após a classificação de intenção."""
    if state.get("error_message"):
        return "handle_error"
    if state["intent"] in ("cep", "weather"):
        return "execute_tool"
    return "format_response"


def route_after_tool_execution(state: AgentState) -> str:
  """Decide o próximo nó após a execução da ferramenta."""
  if state.get("error_message"):
    return "handle_error"
  return "format_response"


def build_graph() -> CompiledStateGraph:
    """Monta e compila o StateGraph."""
    graph = StateGraph(AgentState)

    # Nó 1: classifica intenção e extrai CEP usando LLM
    graph.add_node("classify_intent", classify_intent) 
    # Nó 2: executa a ferramenta correspondente à intenção
    graph.add_node("execute_tool", execute_tool)
    # Nó 3: formata a resposta final de forma amigável e fluida
    graph.add_node("format_response", format_response)
    # Nó de fallback para transformar falhas internas em resposta controlada
    graph.add_node("handle_error", handle_error)
    # Define as transições entre os nós
    graph.add_edge(START, "classify_intent")
    # Roteamento condicional após classificação de intenção
    graph.add_conditional_edges("classify_intent", route_after_classification)
    # Roteamento condicional após execução da ferramenta
    graph.add_conditional_edges("execute_tool", route_after_tool_execution)
    # Transições diretas para formatação de resposta e tratamento de erros
    graph.add_edge("format_response", END)
    # Transição direta para tratamento de erros
    graph.add_edge("handle_error", END)

    return graph.compile()


# Instância compilada do grafo para uso global
agent_graph = build_graph()
