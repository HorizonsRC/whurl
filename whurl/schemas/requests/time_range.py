"""Schema for HilltopServer TimeRange requests."""

from pydantic import Field, field_validator

from whurl.exceptions import HilltopRequestError
from whurl.schemas.mixins import ModelReprMixin
from whurl.schemas.requests.base import BaseHilltopRequest


class TimeRangeRequest(BaseHilltopRequest):
    """Request parameters for Hilltop TimeRange."""

    request: str = Field(default="TimeRange", serialization_alias="Request")
    site: str | None = Field(
        default=None, serialization_alias="Site", validate_default=True
    )
    measurement: str | None = Field(
        default=None, serialization_alias="Measurement", validate_default=True
    )
    format: str | None = Field(default=None, serialization_alias="Format")

    @field_validator("request", mode="before")
    def validate_request(cls, value):
        """Validate the request parameter."""
        if value != "TimeRange":
            raise HilltopRequestError("Request must be 'TimeRange'")
        return value

    @field_validator("site", mode="before")
    def validate_site(cls, value):
        """Validate the site parameter."""
        if not value:
            raise HilltopRequestError("Site parameter is required")
        return value

    @field_validator("measurement", mode="before")
    def validate_measurement(cls, value):
        """Validate the measurement parameter."""
        if not value:
            raise HilltopRequestError("Measurement parameter is required")
        return value

    @field_validator("format", mode="before")
    def validate_format(cls, value):
        """Validate the format parameter."""
        if value and value.lower() != "json":
            raise HilltopRequestError(
                "Format must be 'json' or left blank (default is xml)"
            )
        return value
