"""Schemas de structured output para classificação de intenção pelo LLM."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class PlannerOutput(BaseModel):
    """
    Saída estruturada do Planner Agent.
    Define o plano de ação, qual agente especialista será chamado
    e se ferramentas serão necessárias.
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


class IntentClassification(BaseModel):
    """
    Saída estruturada do nó classificador.
    O LLM deve preencher este schema a partir da mensagem do usuário.
    """

    intent: Literal["cep", "weather", "unknown"] = Field(
        description=(
            "Intenção detectada na mensagem do usuário. "
            "'cep' para consulta de endereço, "
            "'weather' para consulta de clima, "
            "'unknown' para qualquer outra coisa."
        )
    )
    cep: str | None = Field(
        default=None,
        description="CEP de 8 dígitos numéricos extraído da mensagem, sem hífen, se presente.",
    )

    @field_validator("cep", mode="before") #DECORATOR QUE NORMALIZA E VALIDA O CEP ANTES DE ATRIBUIR AO CAMPO
    @classmethod #decorator que indica que o método é um método de classe, ou seja, recebe a classe como primeiro argumento em vez de uma instância
    def normalize_and_validate_cep(cls, v: str | None) -> str | None:
        """Remove hífen e valida que o CEP tem exatamente 8 dígitos numéricos."""
        if v is None:
            return None
        normalized = v.replace("-", "").strip()
        if not normalized.isdigit() or len(normalized) != 8:
            return None
        return normalized


class SpecialistOutput(BaseModel):
    """
    Saída estruturada de um Specialist Agent (CEP ou Weather).
    Valida parâmetros e prepara a ferramenta para execução.
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
    Avalia o resultado da ferramenta e sugere formato de resposta.
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
