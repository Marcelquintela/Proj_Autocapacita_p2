"""Mapeamento de códigos WMO usados pela Open-Meteo."""

WEATHERCODE_PT: dict[int, str] = {
    0: "céu limpo",
    1: "predominantemente limpo",
    2: "parcialmente nublado",
    3: "nublado",
    45: "neblina",
    48: "neblina com geada",
    51: "garoa leve",
    53: "garoa moderada",
    55: "garoa intensa",
    61: "chuva leve",
    63: "chuva moderada",
    65: "chuva intensa",
    71: "neve leve",
    73: "neve moderada",
    75: "neve intensa",
    80: "pancadas de chuva leves",
    81: "pancadas de chuva moderadas",
    82: "pancadas de chuva violentas",
    95: "trovoada",
    96: "trovoada com granizo leve",
    99: "trovoada com granizo intenso",
}


def describe_weather(code: int | None) -> str:
    """Retorna a descrição em português para o weathercode da Open-Meteo."""
    if code is None:
        return "condição desconhecida"
    return WEATHERCODE_PT.get(code, f"código {code}")