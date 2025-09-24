"""Data classes for Hilltop MeasurementList request parameters."""

from pydantic import Field, field_validator

from whurl.exceptions import HilltopRequestError
from whurl.schemas.mixins import ModelReprMixin
from whurl.schemas.requests.base import BaseHilltopRequest


class MeasurementListRequest(BaseHilltopRequest):
    """Request parameters for Hilltop MeasurementList."""

    request: str = Field(default="MeasurementList", serialization_alias="Request")
    site: str | None = Field(default=None, serialization_alias="Site")
    collection: str | None = Field(default=None, serialization_alias="Collection")
    units: str | None = Field(default=None, serialization_alias="Units")
    target: str | None = Field(default=None, serialization_alias="Target")

    @field_validator("request", mode="before")
    def validate_request(cls, value):
        """Validate the request parameter."""
        if value != "MeasurementList":
            raise HilltopRequestError("Request must be 'MeasurementList'")
        return value

    @field_validator("units", mode="before")
    def validate_units(cls, value):
        """
        Validate the units parameter.

        Acceptable values are 'Yes' or None.

        'Yes': Provide units for each measurement.

        """
        if value not in ["Yes", None]:
            raise HilltopRequestError("Units parameter must be 'Yes' or None")
        return value

    @field_validator("target", mode="before")
    def validate_target(cls, value):
        """Validate the target parameter."""
        if value is None:
            return value
        if value != "HtmlSelect":
            raise HilltopRequestError(
                "Only JSON and XML response formats are supported. "
                "Use 'HtmlSelect' to request JSON, or leave it blank for XML."
            )
        if not isinstance(value, str):
            raise HilltopRequestError("Target must be a string")
        return value
