"""Hilltop API Exceptions."""

from typing import Optional, Dict, Any
import httpx


class HilltopError(Exception):
    """Base exception for all Hilltop-related errors."""

    def __init__(self, message: str = "Hilltop API error"):
        self.message = message
        super().__init__(message)


class HilltopHTTPError(HilltopError):
    """Exception for standard HTTP request failures."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        url: Optional[str] = None,
        method: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.status_code = status_code
        self.url = url
        self.method = method
        self.headers = headers
        full_msg = f"{message} [Status: {status_code}]" if status_code else message
        super().__init__(full_msg)


class HilltopResponseError(HilltopError):
    """Exception for Hilltop XML error response."""

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        raw_response: Optional[str] = None,
    ):
        self.raw_response = raw_response
        self.url = url

        # If we know the url, include it in the message
        if url:
            message = f"{message} [URL: {url}]"
        super().__init__(f"Parse error: {message}")


class HilltopParseError(HilltopError):
    """Exception for response parsing failures."""

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        raw_response: Optional[str] = None,
    ):
        self.raw_response = raw_response
        self.url = url

        # If we know the url, include it in the message
        if url:
            message = f"{message} [URL: {url}]"
        super().__init__(f"Parse error: {message}")


class HilltopConfigError(HilltopError):
    """Exception for configuration issues."""

    pass


# Utility function for consistent exception raising
def raise_for_response(response: httpx.Response) -> None:
    """Raise HilltopHTTPError if request failed."""
    if response.is_success:
        return

    try:
        error_detail = response.json().get("error", "Unknown error")
    except ValueError:
        error_detail = response.text or "No error details"

    raise HilltopRequestError(
        message=f"API request failed: {error_detail}",
        status_code=response.status_code,
        url=str(response.url),
        method=response.request.method,
        headers=dict(response.headers),
    )
