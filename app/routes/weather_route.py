"""
Rota responsável por lidar com solicitações relacionadas a informações meteorológicas.
"""

from fastapi import APIRouter

from app.agents.weather_agent import process_weather_request
from app.models.weather_model import WeatherErrorOutput, WeatherLocation, WeatherOutput, WeatherResponse
from app.services.cep_service import get_info_by_cep

router = APIRouter()


@router.get("/weather")
def get_weather(cep: str) -> WeatherResponse:
    """
    Endpoint para obter informações meteorológicas com base nas coordenadas geográficas
    fornecidas pelo CEP.

    Args:
        cep (str): O CEP a ser consultado.

    Returns:
        WeatherResponse: O modelo de sucesso ou erro do agente de clima.
    """
    cep_data = get_info_by_cep(cep)
    if "error" in cep_data:
        return WeatherErrorOutput(message=cep_data["error"])

    latitude = cep_data.get("latitude")
    longitude = cep_data.get("longitude")
    if latitude is None or longitude is None:
        return WeatherErrorOutput(message="Não foi possível obter as coordenadas para o CEP informado.")

    weather = process_weather_request(float(latitude), float(longitude))
    if isinstance(weather, WeatherOutput):
        weather.location = WeatherLocation(
            city=cep_data.get("city"),
            state=cep_data.get("state"),
        )
    return weather
