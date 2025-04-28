"""Hilltop Site List Model."""

from urllib.parse import urlencode, quote
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
import httpx
from urllib.parse import urlencode, quote
import xmltodict
from hurl.exceptions import HilltopParseError, HilltopResponseError, HilltopHTTPError


class HilltopSite(BaseModel):
    """Represents a single Hilltop site."""

    name: str = Field(alias="@Name")


class HilltopSiteList(BaseModel):
    """Top-level Hilltop SiteList response model."""

    agency: str = Field(alias="Agency", default=None)
    version: Optional[str] = Field(alias="Version", default=None)
    site_list: list[HilltopSite] = Field(alias="Site", default_factory=list)
    error: str = Field(alias="Error", default=None)

    @model_validator(mode="after")
    def handle_error(self) -> "HilltopSiteList":
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

    @classmethod
    def from_xml(cls, xml_str: str) -> "HilltopSiteList":
        """Parse XML string into HilltopSiteList object."""
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

    @classmethod
    def from_url(
        cls, url: str, timeout: Optional[int], client: Optional[httpx.Client] = None
    ) -> "HilltopSiteList":
        """Fetch and parse XML from a URL into HilltopSiteList object."""
        if client is None:
            with httpx.Client() as temp_client:
                response = temp_client.get(url, timeout=timeout)
        else:
            response = client.session.get(url, timeout=timeout)

        if response.status_code != 200:
            raise HilltopHTTPError(
                f"Failed to fetch SiteList from Hilltop Server: {response}",
                url=url,
            )
        return cls.from_xml(response.text)

    @classmethod
    def from_params(
        cls,
        base_url: str,
        hts_endpoint: str,
        location: Optional[str] = None,
        bounding_box: Optional[str] = None,
        measurement: Optional[str] = None,
        collection: Optional[str] = None,
        site_parameters: Optional[str] = None,
        target: Optional[str] = None,
        syn_level: Optional[str] = None,
        fill_cols: Optional[str] = None,
        timeout: Optional[int] = 60,
        client: Optional[httpx.Client] = None,
    ) -> "HilltopSiteList":
        """Fetch and parse XML from a URL into HilltopSiteList object."""
        url = gen_site_list_url(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            location=location,
            bounding_box=bounding_box,
            measurement=measurement,
            collection=collection,
            site_parameters=site_parameters,
            target=target,
            syn_level=syn_level,
            fill_cols=fill_cols,
        )
        return cls.from_url(url=url, timeout=timeout, client=client)

    @staticmethod
    def gen_url(
        base_url: str,
        hts_endpoint: str,
        location: Optional[str] = None,
        bounding_box: Optional[str] = None,
        measurement: Optional[str] = None,
        collection: Optional[str] = None,
        site_parameters: Optional[str] = None,
        target: Optional[str] = None,
        syn_level: Optional[str] = None,
        fill_cols: Optional[str] = None,
    ):
        """Generate the URL for the Hilltop SiteList request."""
        return gen_site_list_url(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            location=location,
            bounding_box=bounding_box,
            measurement=measurement,
            collection=collection,
            site_parameters=site_parameters,
            target=target,
            syn_level=syn_level,
            fill_cols=fill_cols,
        )


def gen_site_list_url(
    base_url: str,
    hts_endpoint: str,
    location: Optional[str] = None,
    bounding_box: Optional[str] = None,
    measurement: Optional[str] = None,
    collection: Optional[str] = None,
    site_parameters: Optional[str] = None,
    target: Optional[str] = None,
    syn_level: Optional[str] = None,
    fill_cols: Optional[str] = None,
):
    """Generate the URL for the Hilltop SiteList request."""
    params = {
        "Request": "SiteList",
        "Service": "Hilltop",
        "Location": location,
        "BBox": bounding_box,
        "Measurement": measurement,
        "Collection": collection,
        "SiteParameters": site_parameters,
        "Target": target,
        "SynLevel": syn_level,
        "FillCols": fill_cols,
    }

    selected_params = {key: val for key, val in params.items() if val is not None}

    url = f"{base_url}/{hts_endpoint}?{urlencode(selected_params, quote_via=quote)}"
    return url
