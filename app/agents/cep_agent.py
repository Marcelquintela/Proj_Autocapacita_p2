"""
Agente responsável por processar mensagens relacionadas a endereços.
"""

from app.models.cep_model import (
    CepErrorOutput,
    CepOutput,
    CepResponse,
)
from app.services.cep_service import get_info_by_cep


def process_address_request(cep: str) -> CepResponse:
    """
    Processa uma solicitação de endereço com base no CEP fornecido.

    Args:
        cep (str): O CEP a ser consultado.

    Returns:
        CepResponse: O modelo de sucesso ou erro do agente de endereço.
    """
    data = get_info_by_cep(cep)

    if "error" in data:
        return CepErrorOutput(message=data["error"])

    return CepOutput(
        cep=data.get("cep", ""),
        address_type=data.get("address_type"),
        address_name=data.get("address_name"),
        address=data.get("address"),
        state=data.get("state"),
        district=data.get("district"),
        city=data.get("city"),
        city_ibge=data.get("city_ibge"),
        ddd=data.get("ddd"),
        lat=data.get("latitude"),
        lng=data.get("longitude"),
    )