"""
Serviço que busca coordenadas geograficas a partir de um cep utilizando AwesomeAPI.
"""

import time

import requests

from app.core.config import settings

_CEP_CACHE_TTL_SECONDS = 300
_CEP_CACHE_MAX_ITEMS = 256
_cep_cache: dict[str, tuple[float, dict]] = {}


def _get_cached_cep(normalized_cep: str) -> dict | None:
    """Retorna valor em cache se não estiver expirado."""
    cached = _cep_cache.get(normalized_cep)
    if not cached:
        return None

    timestamp, payload = cached
    if time.time() - timestamp > _CEP_CACHE_TTL_SECONDS:
        _cep_cache.pop(normalized_cep, None)
        return None

    return payload


def _set_cached_cep(normalized_cep: str, payload: dict) -> None:
    """Atualiza cache em memória com política simples de limite."""
    if len(_cep_cache) >= _CEP_CACHE_MAX_ITEMS:
        oldest_key = min(_cep_cache, key=lambda key: _cep_cache[key][0])
        _cep_cache.pop(oldest_key, None)
    _cep_cache[normalized_cep] = (time.time(), payload)


def validate_cep(cep: object) -> dict:
    """
    Valida e normaliza CEP para o formato de 8 dígitos.

    Args:
    cep (object): O CEP a ser validado, pode ser de qualquer tipo.

    Returns:
    dict: Um dicionário contendo o CEP normalizado ou uma mensagem de erro se o
    CEP for inválido.

    """
    if not isinstance(cep, str) or not cep.strip():
        return {"error": "CEP inválido. Informe um CEP em formato texto."}

    normalized_cep = "".join(char for char in cep if char.isdigit())
    if len(normalized_cep) != 8:
        return {"error": "CEP inválido. O CEP deve conter 8 dígitos numéricos."}

    return {"cep": normalized_cep}


def get_info_by_cep(cep: str) -> dict:
    """
    Busca informações de endereço e coordenadas geográficas com base no CEP fornecido.

    Args:
        cep (str): O CEP a ser consultado.
    Returns:
        dict: Um dicionário contendo endereço, coordenadas ou uma mensagem de erro.
        Exemplo de resposta:
                {
                    "cep": "01001000",
                    "address_type": "Praça",
                    "address_name": "da Sé",
                    "address": "Praça da Sé",
                    "state": "SP",
                    "district": "Sé",
                    "lat": "-23.5502784",
                    "lng": "-46.6342179",
                    "city": "São Paulo",
                    "city_ibge": "3550308",
                    "ddd": "11"
                }
            }
    """
    validation = validate_cep(cep)
    if "error" in validation:
        return validation

    normalized_cep = validation["cep"]
    cached = _get_cached_cep(normalized_cep)
    if cached is not None:
        return cached

    lat = None
    lng = None

    url = f"{settings.awesome_api_base_url}/{normalized_cep}?token={settings.awesome_api_token}"

    try:
        response = requests.get(
            url, timeout=5
        )  # Define um tempo limite para a requisição
        response.raise_for_status()  # Verifica se a requisição foi bem-sucedida
        data = response.json()
        lat_raw = data.get("lat")
        lng_raw = data.get("lng")
        
        if lat_raw is not None and lng_raw is not None:
            try:
                lat = float(lat_raw)
                lng = float(lng_raw)
            except (TypeError, ValueError):
                lat = None
                lng = None

        result = {
            "cep": data.get("cep", normalized_cep),
            "address_type": data.get("address_type", ""),
            "address_name": data.get("address_name", ""),
            "address": data.get("address", ""),
            "state": data.get("state", ""),
            "district": data.get("district", ""),
            "latitude": lat,
            "longitude": lng,
            "city": data.get("city", ""),      
            "city_ibge": data.get("city_ibge", ""),
            "ddd": data.get("ddd", ""),
        }
        _set_cached_cep(normalized_cep, result)
        return result
    except requests.RequestException as e:
        return {"error": f"Erro ao buscar dados de CEP: {e}"}
