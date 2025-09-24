"""Hilltop Status Request Model."""

from pydantic import Field, field_validator

from whurl.schemas.mixins import ModelReprMixin
from whurl.schemas.requests.base import BaseHilltopRequest
from whurl.exceptions import HilltopRequestError


class StatusRequest(BaseHilltopRequest):
    """Request parameters for Hilltop status."""

    request: str = Field(default="Status", serialization_alias="Request")

    @field_validator("request", mode="before")
    def validate_request(cls, value):
        """Validate the request parameter."""
        if value != "Status":
            raise HilltopRequestError("Request must be 'Status'")
        return value
