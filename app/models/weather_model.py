"""Contratos de entrada e saída do agente de clima."""

from typing import TypeAlias

from pydantic import BaseModel


class WeatherInput(BaseModel):
    """Entrada do agente de clima baseada em coordenadas."""

    latitude: float
    longitude: float


class WeatherLocation(BaseModel):
    """Localidade usada para contextualizar os dados meteorológicos."""

    city: str | None = None
    state: str | None = None


class WeatherOutput(BaseModel):
    """Saída de sucesso do agente de clima."""

    # Localidade enriquecida a partir da consulta de CEP
    location: WeatherLocation | None = None

    # Dados meteorológicos retornados pela Open-Meteo
    time: str | None = None
    interval: int | None = None
    temperature: float | None = None
    windspeed: float | None = None
    winddirection: int | None = None
    is_day: int | None = None
    weathercode: int | None = None

    # Fonte dos dados
    source: str = "Open-Meteo (https://open-meteo.com)"


class WeatherErrorOutput(BaseModel):
    """Saída de erro do agente de clima."""

    message: str


WeatherResponse: TypeAlias = WeatherOutput | WeatherErrorOutput
