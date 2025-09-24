"""Hilltop SiteList response models."""

from typing import Any

import pandas as pd
import xmltodict
from pydantic import BaseModel, Field, field_validator, model_validator

from whurl.exceptions import HilltopParseError, HilltopResponseError
from whurl.schemas.mixins import ModelReprMixin
from whurl.schemas.requests import SiteListRequest


class SiteListResponse(ModelReprMixin, BaseModel):
    """Top-level Hilltop SiteList response model."""

    class Site(ModelReprMixin, BaseModel):
        """Represents a single Hilltop site."""

        name: str = Field(alias="@Name")
        easting: float | None = Field(alias="Easting", default=None)
        northing: float | None = Field(alias="Northing", default=None)
        latitude: float | None = Field(alias="Latitude", default=None)
        longitude: float | None = Field(alias="Longitude", default=None)

        def to_dict(self):
            """Convert the model to a dictionary."""
            return self.model_dump(exclude_unset=True, by_alias=True)

    agency: str = Field(alias="Agency", default=None)
    version: str | None = Field(alias="Version", default=None)
    crc: str | None = Field(alias="CRC", default=None)
    site_list: list[Site] = Field(alias="Site", default_factory=list)
    error: str = Field(alias="Error", default=None)
    request: SiteListRequest | None = Field(default=None, exclude=True)

    @model_validator(mode="after")
    def handle_error(self) -> "SiteListResponse":
        """Handle errors in the response."""
        if self.error is not None:
            raise HilltopResponseError(
                f"Hilltop SiteList error: {self.error}",
                raw_response=self.model_dump(exclude_unset=True, by_alias=True),
            )
        return self

    def to_dict(self):
        """Convert the model to a dictionary."""
        return self.model_dump(exclude_unset=True, by_alias=True)

    def to_dataframe(self):
        """Convert the model to a pandas DataFrame."""
        data = self.to_dict()
        sites = data.pop("Site", [])
        df = pd.DataFrame(sites)

        df["Agency"] = data["Agency"]
        if "Version" in data:
            df["Version"] = data["Version"]

        return df

    @classmethod
    def from_xml(cls, xml_str: str) -> "SiteListResponse":
        """Parse XML string into SiteListResponse object."""
        response = xmltodict.parse(xml_str)

        if "HilltopServer" not in response:
            raise HilltopParseError(
                "Unexpected Hilltop XML response.",
                raw_response=xml_str,
            )

        data = response["HilltopServer"]

        if "Site" in data:
            if not isinstance(data["Site"], list):
                data["Site"] = [data["Site"]]

        return cls(**data)
