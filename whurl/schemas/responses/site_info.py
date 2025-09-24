"""Hilltop SiteInfo response schema."""

from typing import Any, Dict
from xml.parsers.expat import ExpatError

import xmltodict
from pydantic import BaseModel, Field, model_validator

from whurl.exceptions import HilltopParseError, HilltopResponseError
from whurl.schemas.mixins import ModelReprMixin
from whurl.schemas.requests import SiteInfoRequest
from whurl.utils import sanitise_xml_attributes


class SiteInfoResponse(ModelReprMixin, BaseModel):
    """Represents the response for a Hilltop SiteInfo request."""

    class Site(ModelReprMixin, BaseModel):
        """Represents the info from a single Hilltop Site."""

        name: str = Field(alias="@Name")
        info: Dict[str, Any] = Field(default_factory=dict)

        def to_dict(self):
            """Convert the model to a dictionary."""
            return self.model_dump(exclude_unset=False, by_alias=True)

        @model_validator(mode="before")
        def construct_info_df(cls, data: Dict[str, Any]) -> Dict[str, Any]:
            """Extract dynamic fields from the response."""
            known_fields = {"@Name"}
            dynamic = {k: v for k, v in data.items() if k not in known_fields}

            return {
                "@Name": data.get("@Name"),
                "info": dynamic,
            }

    agency: str = Field(alias="Agency", default=None)
    site: list[Site] = Field(alias="Site", default_factory=list)
    request: SiteInfoRequest | None = Field(default=None, exclude=True)

    @classmethod
    def from_xml(cls, xml_str: str) -> "SiteInfoResponse":
        """Parse the XML string and return a SiteInfoResponse instance."""
        try:
            response = xmltodict.parse(sanitise_xml_attributes(xml_str))
        except ExpatError as e:
            raise HilltopParseError(
                "Failed to parse XML response", raw_response=xml_str
            ) from e

        if "HilltopServer" not in response:
            raise HilltopParseError(
                "Unexpected HilltopServer response format", raw_response=xml_str
            )
        data = response["HilltopServer"]

        if "Site" in data:
            if not isinstance(data["Site"], list):
                data["Site"] = [data["Site"]]

        return cls(**data)

    def to_dataframe(self):
        """Convert the model to a pandas DataFrame."""
        import pandas as pd

        if not self.site:
            raise HilltopParseError("No site data available in the response.")

        df = pd.DataFrame({site.name: site.info for site in self.site})

        return df

    def to_dict(self):
        """Convert the model to a dictionary."""
        return self.model_dump(exclude_unset=True, by_alias=True)
