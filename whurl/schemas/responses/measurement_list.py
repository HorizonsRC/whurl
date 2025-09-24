"""Contains the functions and models for the Hilltop MeasurementList request."""

from datetime import datetime
from typing import List, Optional, Self
from urllib.parse import quote, urlencode

import httpx
import pandas as pd
import xmltodict
from pydantic import BaseModel, Field, field_validator, model_validator

from whurl.exceptions import (HilltopParseError, HilltopRequestError,
                              HilltopResponseError)
from whurl.schemas.mixins import ModelReprMixin
from whurl.schemas.requests import MeasurementListRequest


class MeasurementListResponse(ModelReprMixin, BaseModel):
    """Top-level Hilltop MeasurementList response model."""

    class DataSource(ModelReprMixin, BaseModel):
        """Represents a data source containing measurements."""

        class Measurement(ModelReprMixin, BaseModel):
            """Represents a single Hilltop measurement."""

            name: str = Field(alias="@Name")
            site: str | None = Field(alias="@Site", default=None)
            units: str | None = Field(alias="Units", default=None)
            fmt: str | None = Field(alias="Format", default=None)
            request_as: str | None = Field(alias="RequestAs", default=None)
            measurement_group: str | None = Field(
                alias="MeasurementGroup", default=None
            )
            ratset1: str | None = Field(alias="Ratset1", default=None)
            ratset2: str | None = Field(alias="Ratset2", default=None)
            first_rating: datetime | None = Field(alias="FirstRating", default=None)
            last_rating: datetime | None = Field(alias="LastRating", default=None)
            from_time: datetime | None = Field(alias="From", default=None)
            to_time: datetime | None = Field(alias="To", default=None)
            friendly_name: str | None = Field(alias="FriendlyName", default=None)
            vm: str | None = Field(alias="VM", default=None)
            vm_start: datetime | None = Field(alias="VMStart", default=None)
            vm_finish: datetime | None = Field(alias="VMFinish", default=None)
            divisor: str | None = Field(alias="Divisor", default=None)
            default_measurement: bool | None = Field(
                alias="DefaultMeasurement", default=False, validate_default=False
            )

            @field_validator("default_measurement", mode="before")
            def set_default_measurement(cls, value) -> bool:
                """Set the default measurement to True if field is not unset."""
                return value is None

            def to_dict(self):
                """Convert the model to a dictionary."""
                return self.model_dump(exclude_unset=True, by_alias=True)

        name: str = Field(alias="@Name")
        site: str = Field(alias="@Site")
        num_items: str = Field(alias="NumItems")
        ts_type: str = Field(alias="TSType")
        data_type: str = Field(alias="DataType")
        interpolation: str = Field(alias="Interpolation")
        item_format: str = Field(alias="ItemFormat")
        from_time: datetime = Field(alias="From")
        to_time: datetime = Field(alias="To")
        sensor_group: str | None = Field(alias="SensorGroup", default=None)
        measurements: list["Measurement"] = Field(
            alias="Measurement", default_factory=list
        )

        @field_validator("measurements", mode="before")
        def validate_measurements(cls, value) -> list["Measurement"]:
            """Ensure measurements is a list, even when there is only one."""
            if value is None:
                return []
            if isinstance(value, dict):
                return [cls.Measurement(**value)]
            return [cls.Measurement(**item) for item in value]

        def to_dict(self):
            """Convert the model to a dictionary."""
            return self.model_dump(exclude_unset=True, by_alias=True)

    agency: str | None = Field(alias="Agency", default=None)
    data_sources: list["DataSource"] = Field(alias="DataSource", default_factory=list)
    measurements: list["DataSource.Measurement"] = Field(
        alias="Measurement", default_factory=list
    )
    error: str | None = Field(alias="Error", default=None)
    request: MeasurementListRequest | None = Field(default=None, exclude=True)

    @field_validator("measurements", mode="before")
    def validate_measurements(cls, value) -> list["Measurement"]:
        """Ensure measurements is a list, even when there is only one."""
        if value is None:
            return []
        if isinstance(value, dict):
            return [cls.DataSource.Measurement(**value)]
        return [cls.DataSource.Measurement(**item) for item in value]

    @model_validator(mode="after")
    def handle_error(self) -> "self":
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
    def from_xml(cls, xml_str: str) -> "MeasurementListResponse":
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
