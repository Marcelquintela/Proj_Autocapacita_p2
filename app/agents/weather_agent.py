"""
Agente responsável por processar mensagens relacionadas a informações meteorológicas.
"""

from app.models.weather_model import WeatherErrorOutput, WeatherOutput, WeatherResponse
from app.services.weather_service import get_weather_by_coordinates


def process_weather_request(
    lat: float,
    lng: float,
) -> WeatherResponse:
    """
    Processa uma solicitação de informações meteorológicas com base nas coordenadas geográficas fornecidas.

    Args:
        lat (float): A latitude do local a ser consultado.
        lng (float): A longitude do local a ser consultado.

    Returns:
        WeatherResponse: O modelo de sucesso ou erro do agente de clima.
    """
    weather_data = get_weather_by_coordinates(lat, lng)

    if "error" in weather_data:
        return WeatherErrorOutput(message=weather_data["error"])
    if "message" in weather_data:
        return WeatherErrorOutput(message=weather_data["message"])

    return WeatherOutput(**weather_data)