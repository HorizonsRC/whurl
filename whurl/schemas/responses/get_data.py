"""GetData response schema."""

from __future__ import annotations

from urllib.parse import quote, urlencode

import httpx
import pandas as pd
import xmltodict
from pydantic import (BaseModel, ConfigDict, Field, PrivateAttr,
                      field_validator, model_validator)

from whurl.exceptions import HilltopParseError, HilltopResponseError
from whurl.schemas.mixins import ModelReprMixin
from whurl.schemas.requests import GetDataRequest


class GetDataResponse(ModelReprMixin, BaseModel):
    """Top-level Hilltop GetData response model."""

    class Measurement(ModelReprMixin, BaseModel):
        """Represents a single Hilltop measurement containing data sources and data."""

        class DataSource(ModelReprMixin, BaseModel):
            """Represents a data source containing info about the fields in the data."""

            class ItemInfo(ModelReprMixin, BaseModel):
                """Describes a data type in the data."""

                item_number: int = Field(alias="@ItemNumber")
                item_name: str = Field(alias="ItemName")
                item_format: str = Field(alias="ItemFormat")
                divisor: float | None = Field(alias="Divisor", default=None)
                units: str | None = Field(alias="Units", default=None)
                format: str = Field(alias="Format")

                def to_dict(self):
                    """Convert the model to a dictionary."""
                    return self.model_dump(exclude_unset=True, by_alias=True)

            name: str = Field(alias="@Name")
            num_items: int = Field(alias="@NumItems")
            ts_type: str = Field(alias="TSType")
            data_type: str = Field(alias="DataType")
            interpolation: str = Field(alias="Interpolation")
            item_format: str | None = Field(alias="ItemFormat", default=None)
            item_info: list["ItemInfo"] = Field(alias="ItemInfo", default_factory=list)

            @field_validator("item_info", mode="before")
            def validate_item_info(cls, value: dict | list) -> list["ItemInfo"]:
                """Ensure item_info is a list, even when there is only one."""
                if value is None:
                    return []
                if isinstance(value, dict):
                    return [cls.ItemInfo(**value)]
                return [cls.ItemInfo(**item) for item in value]

            def to_dict(self):
                """Convert the model to a dictionary."""
                return self.model_dump(exclude_unset=True, by_alias=True)

        class Data(ModelReprMixin, BaseModel):
            """Represents the data model containing data points."""

            date_format: str = Field(alias="@DateFormat")
            num_items: int = Field(alias="@NumItems")
            timeseries: pd.DataFrame = Field(alias="E", default_factory=pd.DataFrame)
            _item_info: list["ItemInfo"] = PrivateAttr(default_factory=list)

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
            def construct_dataframe(self) -> "self":
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

        site_name: str = Field(alias="@SiteName")
        data_source: DataSource = Field(alias="DataSource")
        data: Data = Field(alias="Data", default_factory=list)
        tideda_site_number: str | None = Field(alias="TidedaSiteNumber", default=None)

        @model_validator(mode="after")
        def transfer_item_info(self) -> "self":
            """Send item_info from datasource to data."""
            if self.data_source.item_info is not None:
                self.data._item_info = self.data_source.item_info
                self.data.model_validate(self.data)
            return self

    agency: str = Field(alias="Agency", default=None)
    measurement: list[Measurement] = Field(alias="Measurement", default_factory=list)
    error: str | None = Field(alias="Error", default=None)
    request: GetDataRequest | None = Field(default=None, exclude=True)

    @field_validator("measurement", mode="before")
    def validate_measurement(cls, value: dict | list) -> list[Measurement]:
        """Ensure measurement is a list, even when there is only one."""
        if value is None:
            return []
        if isinstance(value, dict):
            return [cls.Measurement(**value)]
        return [cls.Measurement(**item) for item in value]

    def to_dict(self):
        """Convert the model to a dictionary."""
        return self.model_dump(exclude_unset=True, by_alias=True)

    @model_validator(mode="after")
    def handle_error(self) -> "self":
        """Handle errors in the response."""
        if self.error is not None:
            raise HilltopResponseError(
                f"Hilltop MeasurementList error: {self.error}",
                raw_response=self.model_dump(exclude_unset=True, by_alias=True),
            )
        return self

    def to_dataframe(self):
        """Convert the model to a pandas DataFrame."""
        frames = []
        for measurement in self.measurement:
            frame = measurement.data.timeseries
            if not frame.empty:
                frame["Site"] = measurement.site_name
                frame["DataSource"] = measurement.data_source.name
                frames.append(frame)
        if len(frames) == 0:
            return pd.DataFrame()
        else:
            return pd.concat(frames, ignore_index=False)

    @classmethod
    def from_xml(cls, xml_str: str) -> "GetDataResponse":
        """Parse XML string into GetData object."""
        response = xmltodict.parse(xml_str)
        if "HilltopServer" in response:
            # HilltopServer is the root element for Hilltop responses
            # Except for GetData. BUT if it's an error we're back to Hilltop
            data = response["HilltopServer"]
            if "Error" in data:
                raise HilltopResponseError(
                    f"Hilltop GetData error: {data['Error']}",
                    raw_response=xml_str,
                )
            else:
                # This is a Hilltop error response, not a GetData response
                raise HilltopParseError(
                    "Unexpected Hilltop XML response.",
                    raw_response=xml_str,
                )
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
