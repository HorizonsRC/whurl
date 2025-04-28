"""Hilltop status model."""

from typing import List, Optional
from urllib.parse import quote, urlencode

import httpx
import xmltodict
from pydantic import BaseModel, Field


class HilltopDataFile(BaseModel):
    """Represents a Hilltop data file."""

    filename: str = Field(alias="Filename")
    usage_count: Optional[int] = Field(alias="UsageCount", default=None)
    open_for: Optional[int] = Field(alias="OpenFor", default=None)
    full_refresh: Optional[int] = Field(alias="FullRefresh", default=None)
    soft_refresh: Optional[int] = Field(alias="SoftRefresh", default=None)

    def to_dict(self):
        """Convert the model to a dictionary."""
        return self.model_dump(exclude_unset=True, by_alias=True)


class HilltopStatus(BaseModel):
    """Represents the status of a Hilltop server."""

    agency: Optional[str] = Field(alias="Agency", default=None)
    version: Optional[str] = Field(alias="Version", default=None)
    script_name: Optional[str] = Field(alias="ScriptName", default=None)
    default_file: Optional[str] = Field(alias="DefaultFile", default=None)
    relay_url: Optional[str] = Field(alias="RelayURL", default=None)
    process_id: Optional[int] = Field(alias="ProcessID", default=None)
    working_set: Optional[float] = Field(alias="WorkingSet", default=None)
    data_files: Optional[List[HilltopDataFile]] = Field(
        alias="DataFile", default_factory=list
    )

    def to_dict(self):
        """Convert the model to a dictionary."""
        return self.model_dump(exclude_unset=True, by_alias=True)

    @classmethod
    def from_xml(cls, xml_str: str) -> "HilltopStatus":
        """Parse the XML string and return a HilltopStatus object."""
        response = xmltodict.parse(xml_str)

        if "HilltopServer" not in response:
            raise HilltopParseError(
                "Invalid Hilltop server response", raw_response=response
            )

        data = response["HilltopServer"]

        if "DataFile" in data:
            # Ensure DataFile is a list
            if not isinstance(data["DataFile"], list):
                data["DataFile"] = [data["DataFile"]]

        return cls(**data)

    @classmethod
    def from_url(
        cls, url: str, timeout: Optional[int], client: Optional[httpx.Client] = None
    ) -> "HilltopStatus":
        """Fetch the XML from the URL and return a HilltopStatus object."""
        if client is None:
            with httpx.Client() as temp_client:
                response = temp_client.get(url, timeout=timeout)
        else:
            response = client.session.get(url, timeout=timeout)

        if response.status_code != 200:
            raise HilltopHTTPError(
                f"Failed to fetch Status from Hilltop Server: {response}",
                url=url,
            )
        return cls.from_xml(response.text)

    @classmethod
    def from_params(
        cls,
        base_url: str,
        hts_endpoint: str,
        timeout: Optional[int] = 60,
        client: Optional[httpx.Client] = None,
    ) -> "HilltopMeasurementList":
        """Fetch the XML from the URL and return a HilltopStatus object."""
        url = gen_status_url(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        )
        return cls.from_url(url=url, timeout=timeout, client=client)

    @staticmethod
    def gen_url(
        base_url,
        hts_endpoint,
    ):
        """Generate the URL for the Hilltop Status request."""
        return gen_status_url(
            base_url, hts_endpoint
        )


def gen_status_url(
    base_url,
    hts_endpoint,
):
    """Generate the URL for the Hilltop Status request."""
    params = {
        "Request": "Status",
        "Service": "Hilltop",
    }

    selected_params = {key: val for key, val in params.items() if val is not None}

    url = f"{base_url}/{hts_endpoint}?{urlencode(selected_params, quote_via=quote)}"

    return url
