"""
Configuração central do projeto usando Pydantic Settings.
Carrega variáveis de ambiente do arquivo .env.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Carrega variáveis de ambiente de forma tipada e segura.
    """

    # Azure AI Foundry Configuration
    azure_openai_base_url: str
    azure_openai_api_key: str
    azure_openai_chat_deployment: str = "gpt-4.1"

    # AwesomeAPI CEP Configuration
    awesome_api_base_url: str
    awesome_api_token: str
    awesome_api_key_header: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Instância global para importação em qualquer módulo
settings = Settings()
