"""Data classes for Hilltop CollectionList request parameters."""

from pydantic import Field, field_validator

from whurl.exceptions import HilltopRequestError
from whurl.schemas.mixins import ModelReprMixin
from whurl.schemas.requests.base import BaseHilltopRequest


class CollectionListRequest(BaseHilltopRequest):
    """Request parameters for Hilltop CollectionList."""

    request: str = Field(default="CollectionList", serialization_alias="Request")

    @field_validator("request", mode="before")
    def validate_request(cls, value):
        """Validate the request parameter."""
        if value != "CollectionList":
            raise HilltopRequestError("Request must be 'CollectionList'")
        return value
