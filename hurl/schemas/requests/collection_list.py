"""Data classes for Hilltop CollectionList request parameters."""

from pydantic import Field, field_validator

from hurl.schemas.requests.base import BaseHilltopRequest
from hurl.exceptions import HilltopRequestError
from hurl.schemas.mixins import ModelReprMixin


class CollectionListRequest(BaseHilltopRequest):
    """Request parameters for Hilltop CollectionList."""

    request: str = Field(default="CollectionList", serialization_alias="Request")

    @field_validator("request", mode="before")
    def validate_request(cls, value):
        """Validate the request parameter."""
        if value != "CollectionList":
            raise HilltopRequestError("Request must be 'CollectionList'")
        return value
