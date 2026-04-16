"""
Serviço de busca de informações meteorológicas utilizando a API Open-Meteo.
"""

import requests


def validate_coordinates(lat: float, lng: float) -> dict:
    """
    Valida e normaliza as coordenadas geográficas.

    Args:
        lat (float): A latitude a ser validada.
        lng (float): A longitude a ser validada.
    Returns:
        dict: Um dicionário contendo as coordenadas normalizadas ou uma mensagem de erro
    """
    try:
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            return {"error": "Coordenadas inválidas. Latitude deve estar entre -90 e 90, e longitude entre -180 e 180."}
        return {"latitude": lat, "longitude": lng}
    except (TypeError, ValueError):
        return {"error": "Coordenadas inválidas. Informe valores numéricos para latitude e longitude."}

def get_weather_by_coordinates(lat: float, lng: float) -> dict:
    """
    Busca informações meteorológicas com base nas coordenadas geográficas fornecidas.

    Args:
        lat (float): A latitude do local a ser consultado.
        lng (float): A longitude do local a ser consultado.

    Returns:
        dict: Um dicionário contendo as informações meteorológicas ou uma mensagem de erro.
    """
    validation = validate_coordinates(lat, lng)
    if "error" in validation:
        return validation

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": validation["latitude"],
        "longitude": validation["longitude"],
        "current_weather": "true",
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()  # Verifica se a requisição foi bem-sucedida
        data = response.json()
        if "current_weather" in data:
            return data["current_weather"]
        else:
            return {
                "message": "Informações meteorológicas não encontradas para as coordenadas fornecidas."
            }
    except requests.RequestException as e:
        return {"message": f"Erro ao buscar informações meteorológicas: {e}"}
