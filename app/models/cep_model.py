"""Contratos de entrada e saída do agente de endereço."""

from typing import TypeAlias

from pydantic import BaseModel


class CepOutput(BaseModel):
    """Saída de sucesso do agente de endereço."""

    cep: str
    address_type: str | None = None
    address_name: str | None = None
    address: str | None = None
    state: str | None = None
    district: str | None = None
    city: str | None = None
    city_ibge: str | None = None
    ddd: str | None = None
    lat: float | None = None
    lng: float | None = None


class CepErrorOutput(BaseModel):
    """Saída de erro do agente de endereço."""

    message: str


CepResponse: TypeAlias = CepOutput | CepErrorOutput
