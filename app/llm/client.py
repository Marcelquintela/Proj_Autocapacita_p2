"""
Cliente LangChain para Azure OpenAI.
Centraliza a criação do modelo de chat usado pelos nós do grafo.
"""

from functools import lru_cache

from pydantic import SecretStr
from langchain_openai import ChatOpenAI

from app.core.config import settings


@lru_cache(maxsize=1)  # Cacheia a instância do modelo para reutilização eficiente
def get_chat_model() -> ChatOpenAI:
    """
    Retorna uma instância singleton do modelo de chat via Azure AI Foundry.
    Usa o endpoint unificado /openai/v1, compatível com o cliente OpenAI padrão.
    """
    return ChatOpenAI(
        base_url=settings.azure_openai_base_url,
        api_key=SecretStr(settings.azure_openai_api_key),
        model=settings.azure_openai_chat_deployment,
        temperature=0,
    )