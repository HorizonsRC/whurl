"""GetData models and URL generation for Hilltop data."""

import pandas as pd
from pydantic import BaseModel, Field, field_validator, model_validator

from urllib.parse import quote, urlencode


class HilltopData(BaseModel):
    """Represents the data model containing data points."""

    date_format: str = Field(alias="@DateFormat")
    num_items: int = Field(alias="@NumItems")
    data_points: pd.DataFrame = Field(alias="DataPoint")


class HilltopItemInfo(BaseModel):
    """Describes a data type in the data."""

    item_number: int = Field(alias="@ItemNumber")
    item_name: str = Field(alias="ItemName")
    item_format: str = Field(alias="ItemFormat")
    units: str = Field(alias="Units")
    format: str = Field(alias="Format")


class HilltopDataSource(BaseModel):
    """Represents a data source containing item info."""

    name: str = Field(alias="@Name")
    num_items: int = Field(alias="@NumItems")
    ts_type: str = Field(alias="TSType")
    data_type: str = Field(alias="DataType")
    interpolation: str = Field(alias="Interpolation")
    item_info: list[HilltopItemInfo] = Field(alias="ItemInfo", default_factory=list)


class HilltopMeasurement(BaseModel):
    """Represents a single Hilltop measurement containing data sources and data."""

    name: str = Field(alias="@SiteName")
    data_source: list[HilltopDataSource] = Field(
        alias="DataSource", default_factory=list
    )
    data: list[HilltopData] = Field(alias="Data", default_factory=list)


class HilltopGetData(BaseModel):
    """Top-level Hilltop GetData response model."""

    agency: str = Field(alias="Agency", default=None)
    measurement: list[HilltopMeasurement] = Field(
        alias="Measurement", default_factory=list
    )


def get_get_data_url(
    base_url,
    site=None,
    measurement=None,
    from_datetime=None,
    to_datetime=None,
    time_interval=None,
    alignment=None,
    collection=None,
    method=None,
    interval=None,
    gap_tolerance=None,
    show_final=None,
    date_only=None,
    send_as=None,
    agency=None,
    format=None,
    ts_type=None,
    show_quality=None,
):
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

    url = f"{base_url}?{urlencode(selected_params, quote_via=quote)}"
    return url
