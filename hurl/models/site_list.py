"""Hilltop Site List Model."""
from urllib.parse import urlencode, quote
from hurl.utils import get_hilltop_response
from xml.etree import ElementTree
from pydantic import BaseModel, Field, field_validator, model_validator


class HilltopSite(BaseModel):
    """Represents a single Hilltop site."""

    name: str = Field(alias="@Name")


class HilltopSiteList(BaseModel):
    """Top-level Hilltop MeasurementList response model."""

    agency: str = Field(alias="Agency", default=None)
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
    def from_url(cls, url: str, timeout: Optional[int]) -> "HilltopSiteList":
        """Fetch and parse XML from a URL into HilltopSiteList object."""
        success, reponse = get_hilltop_response(url, timeout=timeout)
        if not success:
            raise HilltopHTTPError(
                f"Failed to fetch site list from Hilltop Server: {reponse}",
                url=url,
            )
        return cls.from_xml(response.text)

    @classmethod
    def from_params(
        cls,
        base_url: str,
        location: Optional[str] = None,
        bounding_box: Optional[str] = None,
        measurement: Optional[str] = None,
        collection: Optional[str] = None,
        site_parameters: Optional[str] = None,
        target: Optional[str] = None,
        syn_level: Optional[str] = None,
        fill_cols: Optional[str] = None,
        timeout: Optional[int] = 60,
    ) -> "HilltopSiteList":
        """Fetch and parse XML from a URL into HilltopSiteList object."""
        url = get_site_list_url(
            base_url=base_url,
            location=location,
            bounding_box=bounding_box,
            measurement=measurement,
            collection=collection,
            site_parameters=site_parameters,
            target=target,
            syn_level=syn_level,
            fill_cols=fill_cols,
        )
        success, response = get_hilltop_response(url, timeout=timeout)
        if not success:
            raise HilltopHTTPError(
                f"Failed to fetch site list from Hilltop Server: {response}",
                url=url,
            )
        return cls.from_xml(response)





def get_site_list_url(
    base_url,
    location=None,
    bounding_box=None,
    measurement=None,
    collection=None,
    site_parameters=None,
    target=None,
    syn_level=None,
    fill_cols=None,
):
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

    selected_params = {
        key: val for key, val in params.items() if val is not None
    }

    url = f"{base_url}?{urlencode(selected_params, quote_via=quote)}"
    return url


def get_site_list(
    base_url,
    location=None,
    bounding_box=None,
    measurement=None,
    collection=None,
    site_parameters=None,
    target=None,
    syn_level=None,
    fill_cols=None,
    timeout=60,
):
    url = get_site_list_url(
        base_url,
        location,
        bounding_box,
        measurement,
        collection,
        site_parameters,
        target,
        syn_level,
        fill_cols,
    )
    print(url)

    success, ret_obj = get_hilltop_response(url, timeout=timeout)

    root = ElementTree.fromstring(ret_obj.decode())
    site_list = []
    for child in root.findall("Site"):
        site_list += [child.get("Name")]

    return success, site_list, url
