"""Schemas de structured output para classificação de intenção pelo LLM."""

from typing import Literal

from pydantic import BaseModel, Field


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
        description="CEP de 8 dígitos extraído da mensagem, se presente.",
    )
    reasoning: str = Field(
        description="Breve explicação da classificação feita."
    )
