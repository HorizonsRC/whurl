"""Hilltop SiteList response models."""

import pandas as pd
import xmltodict
from pydantic import BaseModel, Field, field_validator, model_validator

from hurl.exceptions import HilltopParseError, HilltopResponseError


class SiteListResponse(BaseModel):
    """Top-level Hilltop SiteList response model."""

    class Site(BaseModel):
        """Represents a single Hilltop site."""

        name: str = Field(alias="@Name")
        easting: float | None = Field(alias="Easting", default=None)
        northing: float | None = Field(alias="Northing", default=None)

        def to_dict(self):
            """Convert the model to a dictionary."""
            return self.model_dump(exclude_unset=True, by_alias=True)

    agency: str = Field(alias="Agency", default=None)
    version: str | None = Field(alias="Version", default=None)
    projection: str | None = Field(alias="Projection", default=None)
    site_list: list[Site] = Field(alias="Site", default_factory=list)
    error: str = Field(alias="Error", default=None)

    @model_validator(mode="after")
    def handle_error(self) -> "SiteListResponse":
        """Handle errors in the response."""
        if self.error is not None:
            raise HilltopResponseError(
                f"Hilltop SiteList error: {self.error}",
                raw_response=self.model_dump(exclude_unset=True, by_alias=True),
            )
        return self

    @field_validator("site_list", mode="before")
    def validate_site_list(cls, value) -> list[dict[str, any]]:
        """Ensure site_list is a list of HilltopSite objects."""
        if value is None:
            return []
        if isinstance(value, dict):
            return [value]
        return value  # Already a list

    def to_dict(self):
        """Convert the model to a dictionary."""
        return self.model_dump(exclude_unset=True, by_alias=True)

    def to_dataframe(self):
        """Convert the model to a pandas DataFrame."""
        data = self.to_dict()
        sites = data.pop("Site", [])
        df = pd.DataFrame(sites)

        df["Agency"] = data["Agency"]
        df["Version"] = data["Version"]
        if "Projection" in data:
            df["Projection"] = data["Projection"]

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

        if "Error" in data:
            raise HilltopResponseError(
                f"Hilltop SiteList error: {response['Error']}",
                raw_response=xml_str,
            )

        if "Site" in data:
            if not isinstance(data["Site"], list):
                data["Site"] = [data["Site"]]

        return cls(**data)
