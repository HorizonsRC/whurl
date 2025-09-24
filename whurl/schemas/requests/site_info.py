"""Hilltop SiteInfo request schema."""

from pydantic import Field, field_validator

from whurl.exceptions import HilltopRequestError
from whurl.schemas.mixins import ModelReprMixin
from whurl.schemas.requests.base import BaseHilltopRequest


class SiteInfoRequest(BaseHilltopRequest):
    """Hilltop SiteInfo request schema."""

    request: str = Field(default="SiteInfo", serialization_alias="Request")
    site: str | None = Field(default=None, serialization_alias="Site")
    field_list: list[str] | None = Field(serialization_alias="FieldList", default=None)
    collection: str | None = Field(serialization_alias="Collection", default=None)

    @field_validator("request", mode="before")
    def validate_request(cls, value):
        """Validate the request parameter."""
        if value != "SiteInfo":
            raise HilltopRequestError("Request must be 'SiteInfo'")
        return value
