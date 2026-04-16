"""
Constrói e compila o grafo LangGraph do agente de chat.

Arquitetura Multiagente:
  START
    ↓
  planner_node          ← Classifica intent e cria plano
    ↓
  route_after_planner   ← Rota para agente especialista
    ├── cep_specialist_node
    ├── weather_specialist_node
    └── format_response (se unknown)
    ↓
  execute_tool          ← Executa ferramenta (puro, determinístico)
    ↓
  critic_node           ← Avalia resultado da ferramenta
    ↓
  format_response       ← Formata resposta final
    ↓
  END

Com fallbacks para handle_error em caso de falha.
"""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.graph.nodes import (
    planner_node,
    cep_specialist_node,
    weather_specialist_node,
    execute_tool,
    critic_node,
    format_response,
    handle_error,
)
from app.graph.state import AgentState


def route_after_planner(state: AgentState) -> str:
    """
    Decide o próximo nó após o Planner Agent.
    
    Rota para:
    - cep_specialist: se target_agent="cep_specialist"
    - weather_specialist: se target_agent="weather_specialist"
    - format_response: se target_agent="formatter" (intent=unknown)
    - handle_error: se houver erro_message
    """
    if state.get("error_message"):
        return "handle_error"
    
    target = state.get("target_agent", "formatter")
    
    if target == "cep_specialist":
        return "cep_specialist_node"
    elif target == "weather_specialist":
        return "weather_specialist_node"
    else:
        return "format_response"


def route_after_specialist(state: AgentState) -> str:
    """
    Decide o próximo nó após um Specialist Agent.
    
    Rota para:
    - execute_tool: se houver tool_input e needs_tool=True
    - format_response: se não há ferramenta necessária
    - handle_error: se houver erro_message
    """
    if state.get("error_message"):
        return "handle_error"
    
    if state.get("needs_tool") and state.get("tool_input"):
        return "execute_tool"
    else:
        return "format_response"


def route_after_tool_execution(state: AgentState) -> str:
    """
    Decide o próximo nó após a execução da ferramenta.
    
    Rota para:
    - critic_node: sempre (avalia o resultado)
    - handle_error: se houver erro crítico
    """
    if state.get("error_message"):
        # Mesmo com erro, passa para critic avaliar
        return "critic_node"
    return "critic_node"


def build_graph() -> CompiledStateGraph:
    """Monta e compila o StateGraph com arquitetura multiagente."""
    graph = StateGraph(AgentState)

    # ===== NÓSS DO GRAFO =====
    
    # Nó 1: Planner Agent - Classifica intenção e cria plano
    graph.add_node("planner_node", planner_node)
    
    # Nó 2: CEP Specialist - Valida e prepara para CEP
    graph.add_node("cep_specialist_node", cep_specialist_node)
    
    # Nó 3: Weather Specialist - Valida e prepara para Weather
    graph.add_node("weather_specialist_node", weather_specialist_node)
    
    # Nó 4: Tool Executor - Executa ferramenta (determinístico)
    graph.add_node("execute_tool", execute_tool)
    
    # Nó 5: Critic Agent - Avalia resultado
    graph.add_node("critic_node", critic_node)
    
    # Nó 6: Response Formatter - Formata resposta final
    graph.add_node("format_response", format_response)
    
    # Nó de Fallback: Handle Error - Trata erros
    graph.add_node("handle_error", handle_error)

    # ===== ARESTAS (TRANSIÇÕES) =====
    
    # Começa no Planner
    graph.add_edge(START, "planner_node")
    
    # Após Planner: roteamento condicional para especialistas ou direto ao formatter
    graph.add_conditional_edges(
        "planner_node",
        route_after_planner,
        {
            "cep_specialist_node": "cep_specialist_node",
            "weather_specialist_node": "weather_specialist_node",
            "format_response": "format_response",
            "handle_error": "handle_error",
        },
    )
    
    # Após CEP Specialist: roteamento para tool ou formatter
    graph.add_conditional_edges(
        "cep_specialist_node",
        route_after_specialist,
        {
            "execute_tool": "execute_tool",
            "format_response": "format_response",
            "handle_error": "handle_error",
        },
    )
    
    # Após Weather Specialist: roteamento para tool ou formatter
    graph.add_conditional_edges(
        "weather_specialist_node",
        route_after_specialist,
        {
            "execute_tool": "execute_tool",
            "format_response": "format_response",
            "handle_error": "handle_error",
        },
    )
    
    # Após Tool Executor: sempre para Critic
    graph.add_conditional_edges(
        "execute_tool",
        route_after_tool_execution,
        {
            "critic_node": "critic_node",
            "handle_error": "handle_error",
        },
    )
    
    # Após Critic: sempre para formatter
    graph.add_edge("critic_node", "format_response")
    
    # Fim: formatter e handle_error vão para END
    graph.add_edge("format_response", END)
    graph.add_edge("handle_error", END)

    return graph.compile()


# Instância compilada do grafo para uso global
agent_graph = build_graph()

