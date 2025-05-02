"""Hilltop Site List Model."""

from typing import Optional, Self
from urllib.parse import quote, urlencode

import httpx
import xmltodict
from pydantic import BaseModel, Field, field_validator, model_validator

from hurl.exceptions import (HilltopHTTPError, HilltopParseError,
                             HilltopResponseError, HilltopRequestError)
from hurl.models.request_parameters import HilltopRequestParameters


class HilltopSiteListRequestParameters(HilltopRequestParameters):
    """Request parameters for Hilltop SiteList."""

    request: str = Field(default="SiteList", serialization_alias="Request")
    location: Optional[str] = Field(default=None, serialization_alias="Location")
    bounding_box: Optional[str] = Field(default=None, serialization_alias="BBox")
    measurement: Optional[str] = Field(default=None, serialization_alias="Measurement")
    collection: Optional[str] = Field(default=None, serialization_alias="Collection")
    site_parameters: Optional[str] = Field(
        default=None, serialization_alias="SiteParameters"
    )
    target: Optional[str] = Field(default=None, serialization_alias="Target")
    syn_level: Optional[str] = Field(default=None, serialization_alias="SynLevel")
    fill_cols: Optional[str] = Field(default=None, serialization_alias="FillCols")

    @field_validator("request", mode="before")
    def validate_request(cls, value):
        """Validate the request parameter."""
        if value != "SiteList":
            raise ValueError("Request must be 'SiteList'")
        return value

    @field_validator("location", mode="before")
    def validate_location(cls, value):
        """
        Validate the location parameter.

        Acceptable values are 'Yes', 'LatLong', or None.

        'Yes': Provide location in easting and northing format.
        'LatLong': Provide location in latitude and longitude format (NZGD2000).

        """
        if value not in ["Yes", "LatLong", None]:
            raise HilltopRequestError("Location must be 'Yes', 'LatLong', or None")
        return value

    @field_validator("bounding_box", mode="before")
    def validate_bounding_box(cls, value):
        """
        Validate the bounding box parameter.

        The BBox key accepts two easting and northing pairs by default. These define
        two points diagonally opposite to each other. The order of the pairs is not
        important, but the easting precedes the northing in each pair.

        The BBox key can be in lat/long if you wish and you use a shortened version of
        the OGC format. For example to send a bounding box in WGS84:

        >>> BBox=-46.48797124,167.65999182,-44.73293297,168.83236546,EPSG:4326

        Valid EPSG codes are:
        - EPSG:4326 (WGS84)
        - EPSG:2193 (NZTM 2000)
        - EPSG:27200 (NZMG)
        - EPSG:4167 (NZGD 2000)

        """
        if value is not None and not isinstance(value, str):
            raise HilltopRequestError("Bounding box must be a string")

        # Split the bounding box into parts
        parts = value.split(",") if value else []

        if len(parts) < 4:
            raise HilltopRequestError(
                "Bounding box must contain at least four values "
                "(two pairs of coordinates)"
            )
        if len(parts) > 5:
            raise HilltopRequestError(
                "Bounding box must contain at most five values "
                "(two pairs of coordinates and an optional EPSG code)"
            )
        epsg_code = parts[-1] if len(parts) == 5 else None
        coordinates = parts[:-1] if epsg_code else parts

        if epsg_code not in ["EPSG:4326", "EPSG:2193", "EPSG:27200", "EPSG:4167"]:
            raise HilltopRequestError(
                "Invalid EPSG code. Valid codes are: "
                "EPSG:4326 (WGS84), "
                "EPSG:2193 (NZTM 2000), "
                "EPSG:27200 (NZMG), "
                "EPSG:4167 (NZGD 2000). "
                "Disregard the name in the parenthesis, only supply EPSG:XXXX. "
            )

        for coord in coordinates:
            try:
                float(coord)
            except ValueError:
                raise HilltopRequestError(
                    "Bounding box coordinates must be numeric values"
                )

        return value

    @field_validator("target", mode="before")
    def validate_target(cls, value):
        """Validate the target parameter."""
        if value != "HtmlSelect":
            raise HilltopRequestError(
                "Only JSON and XML response formats are supported. "
                "Use 'HtmlSelect' to request JSON, or leave it blank for XML."
            )
        if value is not None and not isinstance(value, str):
            raise HilltopRequestError("Target must be a string")
        return value

    @model_validator(mode="after")
    def validate_syn_level_and_fill_cols(self) -> Self:
        """
        Validate the SynLevel and FillCols parameters.

        SynLevel only valid when 'Target' is 'HtmlSelect'.
        FillCols only valid when SiteParameters are supplied.

        The syn_level key accepts the numbers 1 or 2.
        The FillCols key accepts the word "Yes".

        """
        # Check if the target is 'HtmlSelect'
        if self.target == "HtmlSelect":
            if self.syn_level not in ["1", "2", None]:
                raise HilltopRequestError(
                    "SynLevel must be '1' or '2' or blank when Target is 'HtmlSelect'"
                )
        else:
            # If target is not 'HtmlSelect', syn_level should be None
            if self.syn_level is not None:
                raise HilltopRequestError(
                    "SynLevel must be None when Target is not 'HtmlSelect'"
                )

        if self.site_parameters:
            if self.fill_cols not in ["Yes", None]:
                raise HilltopRequestError(
                    "FillCols must be 'Yes' or left blank when "
                    "SiteParameters are supplied"
                )
        else:
            # If target is not 'HtmlSelect', syn_level should be None
            if self.fill_cols is not None:
                raise HilltopRequestError(
                    "FillCols must be None when no SiteParameters are supplied"
                )

        return self


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
    service: str = "Hilltop",
    request: str = "SiteList",
    **kwargs,
):
    """Generate the URL for the Hilltop SiteList request."""
    validated_params = HilltopSiteListRequestParameters(
        base_url=base_url,
        hts_endpoint=hts_endpoint,
        service=service,
        request=request,
        **kwargs,
    )

    selected_params = validated_params.model_dump(
        exclude_unset=True,
        by_alias=True,
        exclude={"base_url", "hts_endpoint"},
    )

    print(selected_params)

    url = (
        f"{validated_params.base_url}/{validated_params.hts_endpoint}?"
        f"{urlencode(selected_params, quote_via=quote)}"
    )

    return url
