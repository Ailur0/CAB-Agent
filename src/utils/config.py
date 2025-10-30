"""Configuration management for the Change Management System."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Central configuration class for all application settings."""

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Azure Bot Configuration
    MICROSOFT_APP_ID: str = os.getenv("MICROSOFT_APP_ID", "")
    MICROSOFT_APP_PASSWORD: str = os.getenv("MICROSOFT_APP_PASSWORD", "")
    MICROSOFT_APP_TYPE: str = os.getenv("MICROSOFT_APP_TYPE", "MultiTenant")

    # Microsoft Graph API Configuration
    AZURE_CLIENT_ID: str = os.getenv("AZURE_CLIENT_ID", "")
    AZURE_CLIENT_SECRET: str = os.getenv("AZURE_CLIENT_SECRET", "")
    AZURE_TENANT_ID: str = os.getenv("AZURE_TENANT_ID", "")
    AZURE_AUTHORITY: str = f"https://login.microsoftonline.com/{os.getenv('AZURE_TENANT_ID', '')}"
    GRAPH_SCOPES: list = ["https://graph.microsoft.com/.default"]

    # Azure DevOps Configuration
    AZURE_DEVOPS_ORG: str = os.getenv("AZURE_DEVOPS_ORG", "")
    AZURE_DEVOPS_PROJECT: str = os.getenv("AZURE_DEVOPS_PROJECT", "")
    AZURE_DEVOPS_PAT: str = os.getenv("AZURE_DEVOPS_PAT", "")
    
    # TFS/Azure DevOps Server Configuration
    AZURE_DEVOPS_SERVER_URL: str = os.getenv("AZURE_DEVOPS_SERVER_URL", "")
    AZURE_DEVOPS_COLLECTION: str = os.getenv("AZURE_DEVOPS_COLLECTION", "")
    
    # Determine base URL (supports both cloud and on-premises)
    @classmethod
    def get_devops_base_url(cls) -> str:
        """Get the base URL for Azure DevOps/TFS API calls."""
        if cls.AZURE_DEVOPS_SERVER_URL:
            # On-premises TFS/Azure DevOps Server
            return f"{cls.AZURE_DEVOPS_SERVER_URL}/{cls.AZURE_DEVOPS_COLLECTION}"
        else:
            # Azure DevOps Cloud
            return f"https://dev.azure.com/{cls.AZURE_DEVOPS_ORG}"
    
    AZURE_DEVOPS_BASE_URL: str = ""  # Will be set dynamically

    # Storage Configuration
    AZURE_STORAGE_CONNECTION_STRING: str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    COSMOS_DB_ENDPOINT: str = os.getenv("COSMOS_DB_ENDPOINT", "")
    COSMOS_DB_KEY: str = os.getenv("COSMOS_DB_KEY", "")
    COSMOS_DB_DATABASE: str = os.getenv("COSMOS_DB_DATABASE", "change_management")
    COSMOS_DB_CONTAINER: str = os.getenv("COSMOS_DB_CONTAINER", "conversation_references")

    # Bot Server Configuration
    BOT_PORT: int = int(os.getenv("BOT_PORT", "3978"))
    BOT_HOST: str = os.getenv("BOT_HOST", "0.0.0.0")

    # ADK Configuration
    ADK_MODEL: str = os.getenv("ADK_MODEL", "gpt-4o")
    ADK_TEMPERATURE: float = float(os.getenv("ADK_TEMPERATURE", "0.7"))

    # Approval Workflow Configuration
    APPROVAL_TIMEOUT_MINUTES: int = int(os.getenv("APPROVAL_TIMEOUT_MINUTES", "30"))
    ESCALATION_MANAGER_EMAIL: str = os.getenv("ESCALATION_MANAGER_EMAIL", "")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> list[str]:
        """
        Validate that all required configuration values are set.

        Returns:
            List of missing configuration keys.
        """
        required_keys = [
            "OPENAI_API_KEY",
            "MICROSOFT_APP_ID",
            "MICROSOFT_APP_PASSWORD",
            "AZURE_CLIENT_ID",
            "AZURE_CLIENT_SECRET",
            "AZURE_TENANT_ID",
        ]

        missing = []
        for key in required_keys:
            if not getattr(cls, key):
                missing.append(key)

        return missing

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment."""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"


def get_config() -> type[Config]:
    """Get the Config class."""
    return Config


# Validate configuration on import (non-blocking)
missing_config = Config.validate()
if missing_config:
    import warnings
    warnings.warn(
        f"Optional configuration missing: {', '.join(missing_config)}. "
        "Some features may not be available. This is normal if you're only using TFS/Azure DevOps.",
        UserWarning
    )
