"""Contains the functions and models for the Hilltop MeasurementList request."""

import pandas as pd
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from typing import Optional, List, Self
import xmltodict
from urllib.parse import urlencode, quote
import httpx

from hurl.exceptions import HilltopParseError, HilltopResponseError, HilltopHTTPError


class HilltopMeasurement(BaseModel):
    """Represents a single Hilltop measurement."""

    name: str = Field(alias="@Name")
    site: Optional[str] = Field(alias="@Site", default=None)
    units: Optional[str] = Field(alias="Units", default=None)
    fmt: Optional[str] = Field(alias="Format", default=None)
    request_as: Optional[str] = Field(alias="RequestAs", default=None)
    measurement_group: Optional[str] = Field(alias="MeasurementGroup", default=None)
    ratset1: Optional[str] = Field(alias="Ratset1", default=None)
    ratset2: Optional[str] = Field(alias="Ratset2", default=None)
    first_rating: Optional[datetime] = Field(alias="FirstRating", default=None)
    last_rating: Optional[datetime] = Field(alias="LastRating", default=None)
    from_time: Optional[datetime] = Field(alias="From", default=None)
    to_time: Optional[datetime] = Field(alias="To", default=None)
    friendly_name: Optional[str] = Field(alias="FriendlyName", default=None)
    vm: Optional[str] = Field(alias="VM", default=None)
    vm_start: Optional[datetime] = Field(alias="VMStart", default=None)
    vm_finish: Optional[datetime] = Field(alias="VMFinish", default=None)
    divisor: Optional[str] = Field(alias="Divisor", default=None)
    default_measurement: Optional[bool] = Field(
        alias="DefaultMeasurement", default=False, validate_default=False
    )

    @field_validator("default_measurement", mode="before")
    def set_default_measurement(cls, value) -> bool:
        """Set the default measurement to True if field is not unset."""
        return value is None

    def to_dict(self):
        """Convert the model to a dictionary."""
        return self.model_dump(exclude_unset=True, by_alias=True)


class HilltopDataSource(BaseModel):
    """Represents a data source containing measurements."""

    name: str = Field(alias="@Name")
    site: str = Field(alias="@Site")
    num_items: str = Field(alias="NumItems")
    ts_type: str = Field(alias="TSType")
    data_type: str = Field(alias="DataType")
    interpolation: str = Field(alias="Interpolation")
    item_format: str = Field(alias="ItemFormat")
    from_time: datetime = Field(alias="From")
    to_time: datetime = Field(alias="To")
    sensor_group: Optional[str] = Field(alias="SensorGroup", default=None)
    measurements: list[HilltopMeasurement] = Field(
        alias="Measurement", default_factory=list
    )

    @field_validator("measurements", mode="before")
    def validate_measurements(cls, value) -> list[dict[str, any]]:
        """Ensure measurements is a list, even when there is only one."""
        if value is None:
            return []
        if isinstance(value, dict):
            return [value]
        return value  # Already a list

    def to_dict(self):
        """Convert the model to a dictionary."""
        return self.model_dump(exclude_unset=True, by_alias=True)


class HilltopMeasurementList(BaseModel):
    """Top-level Hilltop MeasurementList response model."""

    agency: Optional[str] = Field(alias="Agency", default=None)
    data_sources: Optional[List[HilltopDataSource]] = Field(
        alias="DataSource", default_factory=list
    )
    measurements: Optional[List[HilltopMeasurement]] = Field(
        alias="Measurement", default_factory=list
    )
    error: Optional[str] = Field(alias="Error", default=None)

    @model_validator(mode="after")
    def handle_error(self) -> Self:
        """Handle errors in the response."""
        if self.error is not None:
            raise HilltopResponseError(
                f"Hilltop MeasurementList error: {self.error}",
                raw_response=self.model_dump(exclude_unset=True, by_alias=True),
            )
        return self

    def to_dataframe(self) -> pd.DataFrame:
        """Convert the model to a pandas DataFrame."""
        records = [m.to_dict() for m in self.measurements]
        for ds in self.data_sources:
            # Flatten the measurements into the records
            for measurement in ds.measurements:
                record = measurement.to_dict()
                if "@Site" not in record:
                    record["@Site"] = ds.site
            record["DataSource"] = ds.name
            records.append(record)

        df = pd.DataFrame.from_records(records)

        df.rename(
            columns={
                "@Name": "Measurement Name",
                "@Site": "Site",
            },
            inplace=True,
        )

        return df

    def to_dict(self):
        """Convert the model to a dictionary."""
        return self.model_dump(exclude_unset=True, by_alias=True)

    @classmethod
    def from_xml(cls, xml_str: str) -> "HilltopMeasurementList":
        """Parse the XML string and return a HilltopMeasurementList object."""
        response = xmltodict.parse(xml_str)

        if "HilltopServer" not in response:
            raise HilltopParseError(
                "Unexpected Hilltop XML response.", raw_response=xml_str
            )
        data = response["HilltopServer"]

        if "DataSource" in data:
            if not isinstance(data["DataSource"], list):
                data["DataSource"] = [data["DataSource"]]

        if "Measurement" in data:
            if not isinstance(data["Measurement"], list):
                data["Measurement"] = [data["Measurement"]]

        return cls(**data)

    @classmethod
    def from_url(
        cls, url: str, timeout: Optional[int], client: Optional[httpx.Client] = None
    ) -> "HilltopMeasurementList":
        """Fetch the XML from the URL and return a HilltopMeasurementList object."""
        if client is None:
            with httpx.Client() as temp_client:
                response = temp_client.get(url, timeout=timeout)
        else:
            response = client.session.get(url, timeout=timeout)

        if response.status_code != 200:
            raise HilltopHTTPError(
                f"Failed to fetch measurement list from Hilltop Server: {response}",
                url=url,
            )
        return cls.from_xml(response.text)

    @classmethod
    def from_params(
        cls,
        base_url: str,
        hts_endpoint: str,
        site: Optional[str] = None,
        collection: Optional[str] = None,
        units: Optional[str] = None,
        target: Optional[str] = None,
        timeout: Optional[int] = 60,
        client: Optional[httpx.Client] = None,
    ) -> "HilltopMeasurementList":
        """Fetch the XML from the URL and return a HilltopMeasurementList object."""
        url = gen_measurement_list_url(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site=site,
            collection=collection,
            units=units,
            target=target,
        )
        return cls.from_url(url=url, timeout=timeout, client=client)

    @staticmethod
    def gen_url(
        base_url, hts_endpoint, site=None, collection=None, units=None, target=None
    ):
        """Generate the URL for the Hilltop MeasurementList request."""
        return gen_measurement_list_url(
            base_url, hts_endpoint, site, collection, units, target
        )


def gen_measurement_list_url(
    base_url,
    hts_endpoint,
    site=None,
    collection=None,
    units=None,
    target=None,
):
    """Generate the URL for the Hilltop MeasurementList request."""
    params = {
        "Request": "MeasurementList",
        "Service": "Hilltop",
        "Site": site,
        "Collection": collection,
        "Units": units,
        "Target": target,
    }

    selected_params = {key: val for key, val in params.items() if val is not None}

    url = f"{base_url}/{hts_endpoint}?{urlencode(selected_params, quote_via=quote)}"

    return url
