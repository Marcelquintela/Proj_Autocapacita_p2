"""Schemas de structured output para classificação de intenção pelo LLM."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


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

    @field_validator("cep", mode="before")
    @classmethod
    def normalize_and_validate_cep(cls, v: str | None) -> str | None:
        """Remove hífen e valida que o CEP tem exatamente 8 dígitos numéricos."""
        if v is None:
            return None
        normalized = v.replace("-", "").strip()
        if not normalized.isdigit() or len(normalized) != 8:
            return None
        return normalized
