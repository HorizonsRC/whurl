"""Schema for TimeRange responses."""

from datetime import datetime

import httpx
import xmltodict
from pydantic import BaseModel, Field, field_validator

from whurl.exceptions import HilltopParseError, HilltopResponseError
from whurl.schemas.mixins import ModelReprMixin
from whurl.schemas.requests import TimeRangeRequest


class TimeRangeResponse(ModelReprMixin, BaseModel):
    """Hilltop TimeRange response model."""

    agency: str = Field(alias="Agency")
    site: str = Field(alias="Site")
    measurement: str = Field(alias="Measurement")
    from_time: str | datetime = Field(alias="From")
    to_time: str | datetime = Field(alias="To")
    units: str = Field(alias="Units")
    request: TimeRangeRequest | None = Field(default=None, exclude=True)

    def to_dict(self):
        """Convert the model to a dictionary."""
        return self.model_dump(exclude_unset=True, by_alias=True)

    @field_validator("from_time", "to_time", mode="before")
    def validate_time(cls, value: str) -> datetime:
        """Convert time strings to datetime objects."""
        try:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")
        except ValueError as e:
            raise HilltopResponseError(
                f"Invalid time format: {value}", raw_response=value
            ) from e

    @classmethod
    def from_xml(cls, xml_str: str) -> "MeasurementListResponse":
        """Parse the XML string and return a HilltopMeasurementList object."""
        response = xmltodict.parse(xml_str)

        if "HilltopServer" not in response:
            raise HilltopParseError(
                "Unexpected Hilltop XML response.", raw_response=xml_str
            )
        data = response["HilltopServer"]

        return cls(**data)
