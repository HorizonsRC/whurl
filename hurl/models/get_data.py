"""GetData models and URL generation for Hilltop data."""

from typing import Optional, Self
from urllib.parse import quote, urlencode

import httpx
import pandas as pd
import xmltodict
from pydantic import (BaseModel, ConfigDict, Field, PrivateAttr,
                      field_validator, model_validator)

from hurl.exceptions import HilltopHTTPError, HilltopParseError


class HilltopItemInfo(BaseModel):
    """Describes a data type in the data."""

    item_number: int = Field(alias="@ItemNumber")
    item_name: str = Field(alias="ItemName")
    item_format: str = Field(alias="ItemFormat")
    divisor: Optional[float] = Field(alias="Divisor", default=None)
    units: str = Field(alias="Units")
    format: str = Field(alias="Format")

    def to_dict(self):
        """Convert the model to a dictionary."""
        return self.model_dump(exclude_unset=True, by_alias=True)


class HilltopDataSource(BaseModel):
    """Represents a data source containing info about the fields in the data."""

    name: str = Field(alias="@Name")
    num_items: int = Field(alias="@NumItems")
    ts_type: str = Field(alias="TSType")
    data_type: str = Field(alias="DataType")
    interpolation: str = Field(alias="Interpolation")
    item_format: Optional[str] = Field(alias="ItemFormat", default=None)
    item_info: list[HilltopItemInfo] = Field(alias="ItemInfo", default_factory=list)

    @field_validator("item_info", mode="before")
    def validate_item_info(cls, value: dict | list) -> list[HilltopItemInfo]:
        """Ensure item_info is a list, even when there is only one."""
        if value is None:
            return []
        if isinstance(value, dict):
            return [HilltopItemInfo(**value)]
        return [HilltopItemInfo(**item) for item in value]

    def to_dict(self):
        """Convert the model to a dictionary."""
        return self.model_dump(exclude_unset=True, by_alias=True)


class HilltopData(BaseModel):
    """Represents the data model containing data points."""

    date_format: str = Field(alias="@DateFormat")
    num_items: int = Field(alias="@NumItems")
    timeseries: pd.DataFrame = Field(alias="E", default_factory=pd.DataFrame)
    _item_info: list[HilltopItemInfo] = PrivateAttr(default_factory=list)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("timeseries", mode="before")
    @classmethod
    def parse_data(cls, value: dict | list) -> pd.DataFrame:
        """Parse the data into a DataFrame."""
        if value is None:
            return pd.DataFrame()
        if isinstance(value, dict):
            return pd.DataFrame.from_dict([value])
        return pd.DataFrame.from_records(value)

    @model_validator(mode="after")
    def construct_dataframe(self) -> Self:
        """Rename columns in the DataFrame to match items in ItemInfo."""
        if "T" in self.timeseries.columns:
            mapping = {
                "T": "DateTime",
            }
        else:
            mapping = {}
        if self._item_info is not None:
            for item in self._item_info:
                current_name = f"I{item.item_number}"
                mapping[current_name] = item.item_name
        self.timeseries.rename(columns=mapping, inplace=True)
        if "DateTime" in self.timeseries.columns:
            if self.date_format == "Calendar":
                self.timeseries["DateTime"] = pd.to_datetime(
                    self.timeseries["DateTime"], format="%Y-%m-%dT%H:%M:%S"
                )
            elif self.date_format == "mowsecs":
                mowsecs_offset = 946771200
                # Convert mowsecs to unix time
                self.time_series["DateTime"] = (
                    self.timeseries["DateTime"] - mowsecs_offset
                )
                # Convert unix time to datetime
                self.timeseries["DateTime"] = pd.Timestamp(
                    self.timeseries["DateTime"], unit="s"
                )
            self.timeseries.set_index("DateTime", inplace=True)
        return self

    def to_dict(self):
        """Convert the model to a dictionary."""
        return self.model_dump(exclude_unset=True, by_alias=True)


class HilltopMeasurement(BaseModel):
    """Represents a single Hilltop measurement containing data sources and data."""

    site_name: str = Field(alias="@SiteName")
    data_source: HilltopDataSource = Field(alias="DataSource")
    data: HilltopData = Field(alias="Data", default_factory=list)
    tideda_site_number: Optional[str] = Field(alias="TidedaSiteNumber", default=None)

    @model_validator(mode="after")
    def transfer_item_info(self) -> Self:
        """Send item_info from datasource to data."""
        if self.data_source.item_info is not None:
            self.data._item_info = self.data_source.item_info
            self.data.model_validate(self.data)
        return self


class HilltopGetData(BaseModel):
    """Top-level Hilltop GetData response model."""

    agency: str = Field(alias="Agency", default=None)
    measurement: list[HilltopMeasurement] = Field(
        alias="Measurement", default_factory=list
    )

    @field_validator("measurement", mode="before")
    def validate_measurement(cls, value: dict | list) -> list[HilltopMeasurement]:
        """Ensure measurement is a list, even when there is only one."""
        if value is None:
            return []
        if isinstance(value, dict):
            return [HilltopMeasurement(**value)]
        return [HilltopMeasurement(**item) for item in value]

    def to_dict(self):
        """Convert the model to a dictionary."""
        return self.model_dump(exclude_unset=True, by_alias=True)

    @classmethod
    def from_xml(cls, xml_str: str) -> "HilltopGetData":
        """Parse XML string into HilltopGetData object."""
        response = xmltodict.parse(xml_str)
        if "Hilltop" not in response:
            raise HilltopParseError(
                "Unexpected Hilltop XML response.",
                raw_response=xml_str,
            )
        data = response["Hilltop"]

        if "Error" in data:
            raise HilltopResponseError(
                f"Hilltop GetData error: {response['Error']}",
                raw_response=xml_str,
            )
        return cls(**data)

    @classmethod
    def from_url(
        cls,
        url: str,
        timeout: Optional[int] = None,
        client: Optional[httpx.Client] = None,
    ) -> "HilltopGetData":
        """Fetch data from the Hilltop server using the provided URL."""
        if client is None:
            with https.Client() as temp_client:
                response = temp_client.get(url, timeout=timeout)
        else:
            response = client.session.get(url, timeout=timeout)

        if response.status_code != 200:
            raise HilltopHTTPError(
                f"Failed to fetch GetData from Hilltop server: {response}",
                url=url,
            )
        return cls.from_xml(response.text)

    @classmethod
    def from_params(
        cls,
        base_url: str,
        hts_endpoint: str,
        site: Optional[str] = None,
        measurement: Optional[str] = None,
        from_datetime: Optional[str] = None,
        to_datetime: Optional[str] = None,
        time_interval: Optional[str] = None,
        alignment: Optional[str] = None,
        collection: Optional[str] = None,
        method: Optional[str] = None,
        interval: Optional[str] = None,
        gap_tolerance: Optional[str] = None,
        show_final: Optional[str] = None,
        date_only: Optional[str] = None,
        send_as: Optional[str] = None,
        agency: Optional[str] = None,
        format: Optional[str] = None,
        ts_type: Optional[str] = None,
        show_quality: Optional[str] = None,
        timeout: Optional[int] = None,
        client: Optional[httpx.Client] = None,
    ) -> "HilltopGetData":
        """Fetch data from the Hilltop server using the provided parameters."""
        url = gen_get_data_url(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site=site,
            measurement=measurement,
            from_datetime=from_datetime,
            to_datetime=to_datetime,
            time_interval=time_interval,
            alignment=alignment,
            collection=collection,
            method=method,
            interval=interval,
            gap_tolerance=gap_tolerance,
            show_final=show_final,
            date_only=date_only,
            send_as=send_as,
            agency=agency,
            format=format,
            ts_type=ts_type,
            show_quality=show_quality,
        )

        return cls.from_url(
            url=url,
            timeout=timeout,
            client=client,
        )

    @staticmethod
    def gen_url(
        base_url: str,
        hts_endpoint: str,
        site: Optional[str] = None,
        measurement: Optional[str] = None,
        from_datetime: Optional[str] = None,
        to_datetime: Optional[str] = None,
        time_interval: Optional[str] = None,
        alignment: Optional[str] = None,
        collection: Optional[str] = None,
        method: Optional[str] = None,
        interval: Optional[str] = None,
        gap_tolerance: Optional[str] = None,
        show_final: Optional[str] = None,
        date_only: Optional[str] = None,
        send_as: Optional[str] = None,
        agency: Optional[str] = None,
        format: Optional[str] = None,
        ts_type: Optional[str] = None,
        show_quality: Optional[str] = None,
    ):
        """Generate a URL for the Hilltop GetData request."""
        return gen_get_data_url(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site=site,
            measurement=measurement,
            from_datetime=from_datetime,
            to_datetime=to_datetime,
            time_interval=time_interval,
            alignment=alignment,
            collection=collection,
            method=method,
            interval=interval,
            gap_tolerance=gap_tolerance,
            show_final=show_final,
            date_only=date_only,
            send_as=send_as,
            agency=agency,
            format=format,
            ts_type=ts_type,
            show_quality=show_quality,
        )


def gen_get_data_url(
    base_url: str,
    hts_endpoint: str,
    site: Optional[str] = None,
    measurement: Optional[str] = None,
    from_datetime: Optional[str] = None,
    to_datetime: Optional[str] = None,
    time_interval: Optional[str] = None,
    alignment: Optional[str] = None,
    collection: Optional[str] = None,
    method: Optional[str] = None,
    interval: Optional[str] = None,
    gap_tolerance: Optional[str] = None,
    show_final: Optional[str] = None,
    date_only: Optional[str] = None,
    send_as: Optional[str] = None,
    agency: Optional[str] = None,
    format: Optional[str] = None,
    ts_type: Optional[str] = None,
    show_quality: Optional[str] = None,
):
    """Generate the URL for the Hilltop GetData request."""
    params = {
        "Request": "GetData",
        "Service": "Hilltop",
        "Site": site,
        "Measurement": measurement,
        "From": from_datetime,
        "To": to_datetime,
        "TimeInterval": time_interval,
        "Alignment": alignment,
        "Collection": collection,
        "Method": method,
        "Interval": interval,
        "GapTolerance": gap_tolerance,
        "ShowFinal": show_final,
        "DateOnly": date_only,
        "SendAs": send_as,
        "Agency": agency,
        "Format": format,
        "tsType": ts_type,
        "ShowQuality": show_quality,
    }

    selected_params = {key: val for key, val in params.items() if val is not None}

    url = f"{base_url}/{hts_endpoint}?{urlencode(selected_params, quote_via=quote)}"
    return url
