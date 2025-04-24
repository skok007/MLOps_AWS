from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict


class Settings(BaseSettings):
    # Define your configuration fields here with optional defaults
    environment: str = Field(..., json_schema_extra={"env": "ENVIRONMENT"})
    app_name: str = Field(..., json_schema_extra={"env": "APP_NAME"})
    debug: bool = Field(..., json_schema_extra={"env": "DEBUG"})

    # database config
    # database_url: str = Field(..., json_schema_extra={"env": "DATABASE_URL"})
    postgres_host: str = Field(..., json_schema_extra={"env": "POSTGRES_HOST"})
    postgres_port: int = 5432  # default
    postgres_db: str = Field(..., json_schema_extra={"env": "POSTGRES_DB"})
    postgres_user: str = Field(..., json_schema_extra={"env": "POSTGRES_USER"})
    postgres_password: str = Field(
        ..., 
        json_schema_extra={"env": "POSTGRES_PASSWORD"}
    )

    # ingestion config
    arxiv_api_url: str = Field(..., json_schema_extra={"env": "ARXIV_API_URL"})
    data_path: str = Field(..., json_schema_extra={"env": "DATA_PATH"})

    # Generation model config
    temperature: float = Field(..., json_schema_extra={"env": "TEMPERATURE"})
    top_p: float = Field(..., json_schema_extra={"env": "TOP_P"})
    max_tokens: int = Field(..., json_schema_extra={"env": "MAX_TOKENS"})

    # Comet config for Opik
    opik_api_key: str = Field(..., json_schema_extra={"env": "OPIK_API_KEY"})
    opik_workspace: str = Field(..., json_schema_extra={"env": "OPIK_WORKSPACE"})

    # OpenAI config
    openai_model: str = Field(..., json_schema_extra={"env": "OPENAI_MODEL"})
    openai_api_key: str = Field(..., json_schema_extra={"env": "OPENAI_API_KEY"})

    rag_config: dict = {}

    model_config = ConfigDict(env_file=".env")  # Load variables from .env if they exist

settings = Settings()
