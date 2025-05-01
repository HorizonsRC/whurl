"""Validation models for request parameters."""

from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

from hurl.exceptions import HilltopHTTPError


class HilltopRequestParameters(BaseModel):
    """Base model for Hilltop request parameters."""

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
        """Validate the base URL."""
        result = urlparse(value)
        if not all([result.scheme, result.netloc]):
            raise HilltopHTTPError("Invalid base URL")
        return value

    @field_validator("hts_endpoint", mode="before")
    def validate_hts_endpoint(cls, value):
        """Validate the HTS endpoint."""
        if not value.endswith(".hts"):
            raise HilltopHTTPError("HTS endpoint must end with .hts")
        return value

    @field_validator("service", mode="before")
    def validate_service(cls, value):
        """Validate the service name."""
        if not value:
            raise HilltopHTTPError("Service name cannot be empty")
        if value in ["SOS", "WFS"]:
            raise HilltopHTTPError(
                "SOS and WFS are not currently supported. "
                'Currently only "Hilltop" is supported'
            )
        if value != "Hilltop":
            raise HilltopHTTPError(
                'Unknown service name. Currently only "Hilltop" is supported'
            )
        return value

    @field_validator("request", mode="before")
    def validate_request(cls, value):
        """Validate the request name."""
        if not value:
            raise HilltopHTTPError("Request name cannot be empty")
        if value not in ["Status", "SiteList", "MeasurementList", "GetData"]:
            raise HilltopHTTPError(
                'Unknown request name. Currently only "Status", "SiteList", '
                '"MeasurementList" and "GetData" are supported'
            )
        return value
