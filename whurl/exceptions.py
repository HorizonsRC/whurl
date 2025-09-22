"""Hilltop API Exceptions."""


class HilltopError(Exception):
    """Base exception for all Hilltop-related errors."""

    def __init__(self, message: str = "Hilltop API error"):
        self.message = message
        super().__init__(message)


class HilltopRequestError(HilltopError):
    """Exception for malformed Hilltop API request."""

    def __init__(
        self,
        message: str,
        url: str | None = None,
    ):
        self.url = url
        full_msg = f"{message} [URL: {url}]" if url else message
        super().__init__(full_msg)


class HilltopResponseError(HilltopError):
    """Exception for Hilltop XML error response."""

    def __init__(
        self,
        message: str,
        url: str | None = None,
        raw_response: str | None = None,
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
        url: str | None = None,
        raw_response: str | None = None,
    ):
        self.raw_response = raw_response
        self.url = url

        # If we know the url, include it in the message
        if url:
            message = f"{message} [URL: {url}], Raw response: {raw_response}"
        super().__init__(f"Parse error: {message}")


class HilltopConfigError(HilltopError):
    """Exception for configuration issues."""

    def __init__(self, message: str = "Hilltop configuration error"):
        super().__init__(message)
