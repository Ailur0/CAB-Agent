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

    # Teams Webhook Configuration
    TEAMS_WEBHOOK_URL: str = os.getenv("TEAMS_WEBHOOK_URL", "")
    
    # Power Automate Configuration (optional - for personal messages)
    POWER_AUTOMATE_URL: str = os.getenv("POWER_AUTOMATE_URL", "")
    
    # Azure Bot Configuration - REMOVED (using webhooks instead)
    # MICROSOFT_APP_ID: str = os.getenv("MICROSOFT_APP_ID", "")
    # MICROSOFT_APP_PASSWORD: str = os.getenv("MICROSOFT_APP_PASSWORD", "")
    # MICROSOFT_APP_TYPE: str = os.getenv("MICROSOFT_APP_TYPE", "MultiTenant")

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
    
    @classmethod
    def get_work_item_url(cls, work_item_id: str) -> str:
        """Generate the URL to view a work item in Azure DevOps/TFS."""
        if cls.AZURE_DEVOPS_SERVER_URL:
            # On-premises TFS/Azure DevOps Server
            return f"{cls.AZURE_DEVOPS_SERVER_URL}/{cls.AZURE_DEVOPS_COLLECTION}/{cls.AZURE_DEVOPS_PROJECT}/_workitems/edit/{work_item_id}"
        else:
            # Azure DevOps Cloud
            return f"https://dev.azure.com/{cls.AZURE_DEVOPS_ORG}/{cls.AZURE_DEVOPS_PROJECT}/_workitems/edit/{work_item_id}"
    
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

    # SQL Server Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mssql+pyodbc://localhost/cab_agent?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes")

    # Bot Server Configuration
    BOT_PORT: int = int(os.getenv("BOT_PORT", "3978"))
    BOT_HOST: str = os.getenv("BOT_HOST", "0.0.0.0")

    # OpenAI Model Configuration
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

    # Approval Workflow Configuration
    APPROVAL_TIMEOUT_MINUTES: int = int(os.getenv("APPROVAL_TIMEOUT_MINUTES", "30"))
    ESCALATION_MANAGER_EMAIL: str = os.getenv("ESCALATION_MANAGER_EMAIL", "")

    # PIR (Post Implementation Review) Configuration
    PIR_REMINDER_HOURS: int = int(os.getenv("PIR_REMINDER_HOURS", "24"))
    PIR_ESCALATION_HOURS: int = int(os.getenv("PIR_ESCALATION_HOURS", "48"))
    CHANGE_MANAGER_EMAIL: str = os.getenv("CHANGE_MANAGER_EMAIL", os.getenv("ESCALATION_MANAGER_EMAIL", ""))

    # Email/SMTP Configuration
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "mail.realpage.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "25"))
    SMTP_USE_SSL: bool = os.getenv("SMTP_USE_SSL", "true").lower() == "true"
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "CAB Agent System")
    EMAIL_IS_ACTIVE: bool = os.getenv("EMAIL_IS_ACTIVE", "true").lower() == "true"
    EMAIL_MAX_RETRIES: int = int(os.getenv("EMAIL_MAX_RETRIES", "3"))
    EMAIL_RETRY_DELAY_MINUTES: int = int(os.getenv("EMAIL_RETRY_DELAY_MINUTES", "5"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Google ADK Configuration
    ADK_MODEL: str = os.getenv("ADK_MODEL", "gemini-2.0-flash-exp")
    ADK_TEMPERATURE: float = float(os.getenv("ADK_TEMPERATURE", "0.7"))

    @classmethod
    def validate(cls) -> list[str]:
        """
        Validate that all required configuration values are set.

        Returns:
            List of missing configuration keys.
        """
        # Optional keys - only warn if missing
        optional_keys = [
            "AZURE_CLIENT_ID",
            "AZURE_CLIENT_SECRET",
            "AZURE_TENANT_ID",
            "SMTP_USERNAME",
            "SMTP_PASSWORD",
        ]

        missing = []
        for key in optional_keys:
            if hasattr(cls, key) and not getattr(cls, key):
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
