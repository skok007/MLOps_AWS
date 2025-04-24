# TODO: confirm I can remove this.
import os
import yaml
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class ConfigLoader:
    _config = None

    @classmethod
    def load_config(cls, config_name: str):
        """
        Loads the configuration file from the config/ directory.
        This method caches the configuration to avoid reloading multiple times.
        """
        if cls._config is None:
            # Determine the base path of the configuration directory
            config_path = os.path.join(
                os.path.dirname(__file__), 
                "../config", 
                f"{config_name}.yaml"
            )

            # Load the YAML config file
            with open(config_path, "r") as file:
                cls._config = yaml.safe_load(file)

        return cls._config

    @classmethod
    def get_config_value(cls, key: str, default=None):
        """
        Retrieve a specific config value from the loaded configuration.
        """
        if cls._config is None:
            raise ValueError(
                "Configuration not loaded. Please call load_config first."
            )

        return cls._config.get(key, default)


def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables.
    
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    config = {
        "environment": os.getenv("ENVIRONMENT", "development"),
        "app_name": os.getenv("APP_NAME", "rag-app"),
        "debug": os.getenv("DEBUG", "False").lower() == "true",
        
        # Database config
        "postgres_host": os.getenv("POSTGRES_HOST", "localhost"),
        "postgres_port": int(os.getenv("POSTGRES_PORT", "5432")),
        "postgres_db": os.getenv("POSTGRES_DB", "rag_db"),
        "postgres_user": os.getenv("POSTGRES_USER", "postgres"),
        "postgres_password": os.getenv("POSTGRES_PASSWORD", "postgres"),
        
        # Ingestion config
        "arxiv_api_url": os.getenv(
            "ARXIV_API_URL", 
            "http://export.arxiv.org/api/query"
        ),
        "data_path": os.getenv("DATA_PATH", "./data"),
        
        # Generation model config
        "temperature": float(os.getenv("TEMPERATURE", "0.7")),
        "top_p": float(os.getenv("TOP_P", "1.0")),
        "max_tokens": int(os.getenv("MAX_TOKENS", "200")),
        
        # Comet config for Opik
        "opik_api_key": os.getenv("OPIK_API_KEY", ""),
        "opik_workspace": os.getenv("OPIK_WORKSPACE", ""),
        
        # OpenAI config
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    }
    
    return config
