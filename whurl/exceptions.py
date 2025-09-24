"""Hilltop API Exceptions.

This module defines custom exception classes for handling various error
conditions that can occur when interacting with Hilltop Server APIs.
"""


class HilltopError(Exception):
    """Base exception for all Hilltop-related errors.

    This is the base exception class that all other Hilltop-specific
    exceptions inherit from. Use this to catch any Hilltop-related error.

    Parameters
    ----------
    message : str, default "Hilltop API error"
        Human-readable error message.
    """

    def __init__(self, message: str = "Hilltop API error"):
        self.message = message
        super().__init__(message)


class HilltopRequestError(HilltopError):
    """Exception for malformed Hilltop API request.

    Raised when request validation fails, such as invalid parameters,
    malformed URLs, or unsupported request types.

    Parameters
    ----------
    message : str
        Human-readable error message describing the validation failure.
    url : str, optional
        The URL that caused the error, if available.

    Attributes
    ----------
    url : str or None
        The URL that caused the error.
    """

    def __init__(
        self,
        message: str,
        url: str | None = None,
    ):
        self.url = url
        full_msg = f"{message} [URL: {url}]" if url else message
        super().__init__(full_msg)


class HilltopResponseError(HilltopError):
    """Exception for Hilltop HTTP response errors.

    Raised when the server returns an HTTP error status code or when
    the response content indicates an error condition.

    Parameters
    ----------
    message : str
        Human-readable error message describing the HTTP error.
    url : str, optional
        The URL that caused the error, if available.
    raw_response : str, optional
        The raw response content from the server.

    Attributes
    ----------
    url : str or None
        The URL that caused the error.
    raw_response : str or None
        The raw response content from the server.
    """

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
    """Exception for response parsing failures.

    Raised when the XML or JSON response from the server cannot be parsed
    or does not conform to the expected structure.

    Parameters
    ----------
    message : str
        Human-readable error message describing the parsing failure.
    url : str, optional
        The URL that generated the unparseable response, if available.
    raw_response : str, optional
        The raw response content that could not be parsed.

    Attributes
    ----------
    url : str or None
        The URL that generated the unparseable response.
    raw_response : str or None
        The raw response content that could not be parsed.
    """

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
    """Exception for configuration issues.

    Raised when required configuration parameters are missing or invalid,
    such as missing environment variables or invalid client settings.

    Parameters
    ----------
    message : str, default "Hilltop configuration error"
        Human-readable error message describing the configuration issue.
    """

    def __init__(self, message: str = "Hilltop configuration error"):
        super().__init__(message)
