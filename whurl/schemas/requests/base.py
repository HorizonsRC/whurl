"""Validation models for Hilltop request parameters.

This module provides the base request model and common validation logic
for all Hilltop API requests.
"""

from urllib.parse import quote, urlencode, urlparse

from pydantic import BaseModel, Field, field_validator

from whurl.exceptions import HilltopRequestError
from whurl.schemas.mixins import ModelReprMixin


class BaseHilltopRequest(ModelReprMixin, BaseModel):
    """Base model for Hilltop request parameters.

    This class provides common fields and validation logic shared by all
    Hilltop API request types. It handles URL generation and parameter
    serialization according to Hilltop Server requirements.

    Parameters
    ----------
    base_url : str, default "http://example.com"
        Base URL for the Hilltop server.
    hts_endpoint : str, default "foo.hts"
        HTS endpoint filename (must end with '.hts').
    service : str, default "Hilltop"
        Service name for the API request.
    request : str, default "Status"
        Request type identifier.
    """

    base_url: str = Field(
        default="http://example.com", description="Base URL for the Hilltop client."
    )
    hts_endpoint: str = Field(
        default="foo.hts", description="HTS endpoint for the Hilltop client."
    )
    service: str = Field(
        default="Hilltop",
        serialization_alias="Service",
        description="Service name for the Hilltop client.",
    )
    request: str = Field(
        default="Status",
        serialization_alias="Request",
        description="Request name for the Hilltop client.",
    )

    @field_validator("base_url", mode="before")
    def validate_base_url(cls, value):
        """Validate the base URL format.

        Parameters
        ----------
        value : str
            The base URL to validate.

        Returns
        -------
        str
            The validated base URL.

        Raises
        ------
        HilltopRequestError
            If the URL format is invalid (missing scheme or netloc).
        """
        result = urlparse(value)
        if not all([result.scheme, result.netloc]):
            raise HilltopRequestError("Invalid base URL")
        return value

    @field_validator("hts_endpoint", mode="before")
    def validate_hts_endpoint(cls, value):
        """Validate the HTS endpoint filename.

        Parameters
        ----------
        value : str
            The HTS endpoint filename to validate.

        Returns
        -------
        str
            The validated HTS endpoint filename.

        Raises
        ------
        HilltopRequestError
            If the endpoint does not end with '.hts'.
        """
        if not value.endswith(".hts"):
            raise HilltopRequestError("HTS endpoint must end with .hts")
        return value

    @field_validator("service", mode="before")
    def validate_service(cls, value):
        """Validate the service name.

        Parameters
        ----------
        value : str
            The service name to validate.

        Returns
        -------
        str
            The validated service name.

        Raises
        ------
        HilltopRequestError
            If the service name is empty or unsupported.
        """
        if not value:
            raise HilltopRequestError("Service name cannot be empty")
        if value in ["SOS", "WFS"]:
            raise HilltopRequestError(
                "SOS and WFS are not currently supported. "
                'Currently only "Hilltop" is supported'
            )
        if value != "Hilltop":
            raise HilltopRequestError(
                'Unknown service name. Currently only "Hilltop" is supported'
            )
        return value

    @field_validator("request", mode="before")
    def validate_request(cls, value):
        """Validate the request type name.

        Parameters
        ----------
        value : str
            The request type name to validate.

        Returns
        -------
        str
            The validated request type name.

        Raises
        ------
        HilltopRequestError
            If the request type is empty or unsupported.
        """
        if not value:
            raise HilltopRequestError("Request name cannot be empty")
        if value not in ["Status", "SiteList", "MeasurementList", "GetData"]:
            raise HilltopRequestError(
                'Unknown request name. Currently only "Status", "SiteList", '
                '"MeasurementList" and "GetData" are supported'
            )
        return value

    def gen_url(self) -> str:
        """Generate the complete URL for the Hilltop request.

        Combines the base URL, HTS endpoint, and request parameters into
        a properly formatted URL suitable for making HTTP requests to
        the Hilltop Server.

        Returns
        -------
        str
            The complete URL with encoded query parameters.
        """
        selected_params = self.model_dump(
            exclude_none=True,
            by_alias=True,
            exclude={"base_url", "hts_endpoint"},
        )

        url = (
            f"{self.base_url}/{self.hts_endpoint}?"
            f"{urlencode(selected_params, quote_via=quote)}"
        )

        return url
