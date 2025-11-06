"""Authentication utilities for Google Cloud and Microsoft services."""

import msal
import requests
import time
from typing import Optional, Dict, Any
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from .config import Config
from .logging_config import get_logger

logger = get_logger(__name__)


class MicrosoftAuthClient:
    """Client for Microsoft Graph API authentication using MSAL."""

    def __init__(self):
        """Initialize the Microsoft authentication client."""
        self.client_id = Config.AZURE_CLIENT_ID
        self.client_secret = Config.AZURE_CLIENT_SECRET
        self.authority = Config.AZURE_AUTHORITY
        self.scopes = Config.GRAPH_SCOPES
        self._token_cache: Optional[Dict[str, Any]] = None

        self.app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            authority=self.authority,
            client_credential=self.client_secret,
        )

    def get_access_token(self) -> str:
        """
        Acquire an access token for Microsoft Graph API.

        Returns:
            Access token string.

        Raises:
            Exception: If token acquisition fails.
        """
        # Try to get token from cache first
        result = self.app.acquire_token_silent(self.scopes, account=None)

        # If not in cache, acquire new token
        if not result:
            logger.info("Acquiring new Microsoft Graph access token")
            result = self.app.acquire_token_for_client(scopes=self.scopes)

        if "access_token" in result:
            logger.debug("Successfully acquired Microsoft Graph access token")
            return result["access_token"]
        else:
            error_msg = result.get("error_description", "Unknown error")
            logger.error("Failed to acquire token", error=error_msg)
            raise Exception(f"Failed to acquire Microsoft Graph token: {error_msg}")

    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers with Bearer token for API requests.

        Returns:
            Dictionary with Authorization header.
        """
        token = self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def call_graph_api(
        self, endpoint: str, method: str = "GET", data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to Microsoft Graph API.

        Args:
            endpoint: API endpoint (e.g., '/users' or full URL).
            method: HTTP method (GET, POST, PATCH, DELETE).
            data: Optional request body for POST/PATCH requests.

        Returns:
            JSON response from the API.

        Raises:
            requests.HTTPError: If the request fails.
        """
        if not endpoint.startswith("https://"):
            endpoint = f"https://graph.microsoft.com/v1.0{endpoint}"

        headers = self.get_auth_headers()

        logger.info("Calling Microsoft Graph API", endpoint=endpoint, method=method)

        response = requests.request(
            method=method, url=endpoint, headers=headers, json=data
        )

        response.raise_for_status()
        return response.json()


class GoogleAuthClient:
    """Client for Google Cloud authentication using service accounts."""

    def __init__(self):
        """Initialize the Google authentication client."""
        self.credentials_path = Config.GOOGLE_APPLICATION_CREDENTIALS
        self._credentials: Optional[service_account.Credentials] = None

    def get_credentials(
        self, scopes: Optional[list[str]] = None
    ) -> service_account.Credentials:
        """
        Get Google Cloud service account credentials.

        Args:
            scopes: Optional list of OAuth2 scopes.

        Returns:
            Service account credentials.

        Raises:
            FileNotFoundError: If credentials file not found.
        """
        if not self.credentials_path:
            raise ValueError(
                "GOOGLE_APPLICATION_CREDENTIALS not set in environment variables"
            )

        if not self._credentials:
            logger.info("Loading Google Cloud credentials", path=self.credentials_path)

            if scopes:
                self._credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path, scopes=scopes
                )
            else:
                self._credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path
                )

        # Refresh if expired
        if self._credentials.expired:
            logger.info("Refreshing expired Google Cloud credentials")
            self._credentials.refresh(Request())

        return self._credentials


class AzureDevOpsAuthClient:
    """Client for Azure DevOps API authentication."""

    def __init__(self):
        """Initialize the Azure DevOps authentication client."""
        self.org = Config.AZURE_DEVOPS_ORG
        self.project = Config.AZURE_DEVOPS_PROJECT
        self.pat = Config.AZURE_DEVOPS_PAT
        self.base_url = Config.get_devops_base_url()
        self.collection = Config.AZURE_DEVOPS_COLLECTION
        self.server_url = Config.AZURE_DEVOPS_SERVER_URL

    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers with PAT authentication for Azure DevOps.

        Returns:
            Dictionary with Authorization header.
        """
        import base64

        # Azure DevOps uses Basic auth with PAT
        auth_string = f":{self.pat}"
        encoded = base64.b64encode(auth_string.encode()).decode()

        return {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json",
        }

    def call_api(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict] = None,
        api_version: str = "7.0",
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        Make an authenticated request to Azure DevOps API with retry logic.

        Args:
            endpoint: API endpoint (relative to project).
            method: HTTP method.
            data: Optional request body.
            api_version: Azure DevOps API version.
            max_retries: Maximum number of retry attempts for transient errors.

        Returns:
            JSON response from the API.

        Raises:
            requests.HTTPError: If the request fails after all retries.
        """
        url = f"{self.base_url}/{self.project}/_apis/{endpoint}?api-version={api_version}"
        headers = self.get_auth_headers()

        logger.info("Calling Azure DevOps API", endpoint=endpoint, method=method)

        last_error = None
        for attempt in range(max_retries):
            try:
                response = requests.request(method=method, url=url, headers=headers, json=data, timeout=30)

                try:
                    response.raise_for_status()
                except requests.HTTPError as e:
                    # Log response body for debugging
                    try:
                        error_detail = response.json()
                        logger.error(
                            "Azure DevOps API error",
                            status_code=response.status_code,
                            error_detail=error_detail,
                            endpoint=endpoint,
                            attempt=attempt + 1,
                        )
                    except:
                        logger.error(
                            "Azure DevOps API error",
                            status_code=response.status_code,
                            response_text=response.text[:500],
                            endpoint=endpoint,
                            attempt=attempt + 1,
                        )
                    
                    # Retry on rate limiting (429) or server errors (5xx)
                    if response.status_code in [429, 500, 502, 503, 504] and attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        logger.warning(
                            "Retrying after error",
                            status_code=response.status_code,
                            wait_time=wait_time,
                            attempt=attempt + 1,
                        )
                        time.sleep(wait_time)
                        continue
                    raise
                
                return response.json()
                
            except requests.exceptions.RequestException as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(
                        "Request failed, retrying",
                        error=str(e),
                        wait_time=wait_time,
                        attempt=attempt + 1,
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error("Request failed after all retries", error=str(e))
                    raise
        
        # Should not reach here, but just in case
        if last_error:
            raise last_error
        raise Exception("Unexpected error in API call")


# Lazy-loaded singleton instances
_microsoft_auth = None
_google_auth = None
_azure_devops_auth = None


def get_microsoft_auth() -> MicrosoftAuthClient:
    """Get or create Microsoft Graph authentication client."""
    global _microsoft_auth
    if _microsoft_auth is None:
        _microsoft_auth = MicrosoftAuthClient()
    return _microsoft_auth


def get_google_auth() -> GoogleAuthClient:
    """Get or create Google Cloud authentication client."""
    global _google_auth
    if _google_auth is None:
        _google_auth = GoogleAuthClient()
    return _google_auth


def get_azure_devops_auth() -> AzureDevOpsAuthClient:
    """Get or create Azure DevOps authentication client."""
    global _azure_devops_auth
    if _azure_devops_auth is None:
        _azure_devops_auth = AzureDevOpsAuthClient()
    return _azure_devops_auth


# Backward compatibility - these will be created on first access
microsoft_auth = property(lambda self: get_microsoft_auth())
google_auth = property(lambda self: get_google_auth())
azure_devops_auth = get_azure_devops_auth()
