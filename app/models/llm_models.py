"""Schemas de structured output usados pelos agentes LLM da V2 multiagente."""

from typing import Literal

from pydantic import BaseModel, Field


class PlannerOutput(BaseModel):
    """
    Saída estruturada do Planner Agent.

    O planner decide intenção, próximo agente, necessidade de ferramenta,
    parâmetros básicos extraídos da mensagem (como CEP) e plano textual.
    """

    intent: Literal["cep", "weather", "unknown"] = Field(
        description="Intenção detectada na mensagem do usuário."
    )
    target_agent: Literal["cep_specialist", "weather_specialist", "formatter"] = Field(
        description="Qual agente especialista será responsável pela próxima etapa."
    )
    needs_tool: bool = Field(
        description="Indica se a execução requer uma ferramenta (API/função determinística)."
    )
    tool_name: str | None = Field(
        default=None,
        description="Nome da ferramenta a ser executada, se needs_tool=True."
    )
    cep: str | None = Field(
        default=None,
        description="CEP extraído da mensagem, se presente."
    )
    plan: str = Field(
        description="Descrição textual do plano de ação decidido pelo planner."
    )


class SpecialistOutput(BaseModel):
    """
    Saída estruturada de um Specialist Agent (CEP ou Weather).

    O especialista valida o contexto de domínio e prepara o tool_input
    para execução determinística.
    """

    is_ready: bool = Field(
        description="Indica se todos os parâmetros necessários estão presentes e válidos."
    )
    tool_input: dict | None = Field(
        default=None,
        description="Parâmetros prontos para serem passados à ferramenta (se is_ready=True)."
    )
    specialist_notes: str = Field(
        description="Anotações técnicas sobre a validação (sucesso ou motivo da falha)."
    )


class CriticOutput(BaseModel):
    """
    Saída estruturada do Critic Agent.

    O crítico avalia consistência semântica do resultado e sinaliza
    o estilo recomendado para resposta final.
    """

    is_valid: bool = Field(
        description="Indica se o resultado obtido é válido e coerente."
    )
    critic_notes: str = Field(
        description="Análise detalhada do resultado (coerência, integridade, falhas semânticas)."
    )
    response_style: Literal["success", "partial", "error"] = Field(
        description="Sugestão de estilo para a resposta final: 'success' (tudo ok), 'partial' (dados incompletos), 'error' (falha)."
    )
