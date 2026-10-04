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
from whurl.utils import MOWSECS_OFFSET


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

class DataType(ModelReprMixin, BaseModel):
    
    data_type_interval: str = Field(alias="@DataTypeInterval")
    data_type: str = Field(alias="#text")

    def to_dict(self):
        """Convert the model to a dictionary."""
        return self.model_dump(exclude_unset=True, by_alias=True)

class GetDataResponse(ModelReprMixin, BaseModel):
    """Top-level Hilltop GetData response model."""

    class Measurement(ModelReprMixin, BaseModel):
        """Represents a single Hilltop measurement containing data sources and data."""

        class DataSource(ModelReprMixin, BaseModel):
            """Represents a data source containing info about the fields in the data."""


            name: str = Field(alias="@Name")
            num_items: int = Field(alias="@NumItems")
            ts_type: str = Field(alias="TSType")
            data_type: DataType | str = Field(alias="DataType")
            interpolation: str = Field(alias="Interpolation")
            item_format: str | None = Field(alias="ItemFormat", default=None)
            item_info: list[ItemInfo] = Field(alias="ItemInfo", default_factory=list)

            @field_validator("item_info", mode="before")
            def validate_item_info(cls, value: dict | list) -> list["ItemInfo"]:
                """Ensure item_info is a list, even when there is only one."""
                if value is None:
                    return []
                if isinstance(value, dict):
                    return [ItemInfo(**value)]
                return [ItemInfo(**item) for item in value]

            def to_dict(self):
                """Convert the model to a dictionary."""
                return self.model_dump(exclude_unset=True, by_alias=True)

        class Data(ModelReprMixin, BaseModel):
            """Represents the data model containing data points."""

            date_format: str = Field(alias="@DateFormat")
            num_items: int = Field(alias="@NumItems")
            timeseries: pd.DataFrame = Field(alias="E", default_factory=pd.DataFrame)
            item_info: list[ItemInfo] = Field(default_factory=list, exclude=True)

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

            @field_validator("item_info", mode="before")
            def validate_item_info(cls, value: dict | list) -> list["ItemInfo"]:
                """Ensure item_info is a list, even when there is only one."""
                if value is None:
                    return []
                if isinstance(value, dict):
                    return [ItemInfo(**value)]
                return [ItemInfo(**item) for item in value]

            @model_validator(mode="after")
            def construct_dataframe(self) -> "self":
                """Rename columns in the DataFrame to match items in ItemInfo."""
                if "T" in self.timeseries.columns:
                    mapping = {
                        "T": "DateTime",
                    }
                else:
                    mapping = {}
                formatter = {}
                divisor = {}
                if self.item_info is not None:
                    for item in self.item_info:
                        current_name = f"I{item.item_number}"
                        mapping[current_name] = item.item_name
                        formatter[item.item_name] = item.item_format
                        divisor[item.item_name] = item.divisor
                self.timeseries.rename(columns=mapping, inplace=True)

                # Apply formatting and divisors
                for col, fmt in formatter.items():
                    if fmt == "I":
                        # Parse as integer
                        self.timeseries[col] = (
                            pd.to_numeric(self.timeseries[col], errors="coerce")
                            .fillna(0)
                            .astype(int)
                        ) / int(divisor.get(col, 1) or 1)
                    elif fmt == "F":
                        # Parse as float
                        self.timeseries[col] = (
                            pd.to_numeric(self.timeseries[col], errors="coerce")
                            .fillna(0.0)
                            .astype(float)
                        ) / float(divisor.get(col, 1.0) or 1.0)
                    elif fmt == "D":
                        try:
                            self.timeseries[col] = pd.to_datetime(
                                self.timeseries[col], format="%Y-%m-%dT%H:%M:%S.f", errors="raise"
                            )
                        except ValueError:
                            try:
                                self.timeseries[col] = pd.to_datetime(
                                    self.timeseries[col], format="%Y-%m-%d %H:%M:%S",
                                )
                            except ValueError:
                                mowsecs_offset = 946771200
                                # Convert mowsecs to unix time
                                time_ints = pd.to_numeric(
                                    self.timeseries[col], errors="coerce"
                                ).fillna(0)
                                self.timeseries[col] = time_ints - mowsecs_offset
                                # Convert unix time to datetime
                                self.timeseries[col] = pd.to_datetime(
                                    self.timeseries[col],
                                    unit="s",
                                    origin="unix",
                                    utc=False,
                                )
                    elif fmt == "S":
                        # Parse as string. 
                        # "string" uses pandas' nullable dtype which prepresents
                        # missing values as pd.NA
                        self.timeseries[col] = self.timeseries[col].astype("string")
                    else:
                        raise HilltopParseError(f"Unknown Format Spec: {fmt}")

                if "DateTime" in self.timeseries.columns:
                    if self.date_format == "Calendar":
                        try:
                            self.timeseries["DateTime"] = pd.to_datetime(
                                self.timeseries["DateTime"], format="%Y-%m-%dT%H:%M:%S", errors="raise"
                            )
                        except ValueError:
                            try:
                                # Try without T
                                self.timeseries["DateTime"] = pd.to_datetime(
                                    self.timeseries["DateTime"], format="%Y-%m-%d %H:%M:%S", errors="raise"
                                )
                            except ValueError:
                                try:
                                    # Try to remove milliseconds
                                    self.timeseries["DateTime"] = pd.to_datetime(
                                        self.timeseries["DateTime"].str.replace(r'\.\d+$', '', regex=True),
                                        format="%Y-%m-%d %H:%M:%S",
                                        errors="raise"
                                    )
                                except ValueError as e:
                                    raise HilltopParseError(f"Unknown date format: {str(e)}")
                            
                    elif self.date_format == "mowsecs":
                        # Convert mowsecs to unix time
                        time_ints = pd.to_numeric(
                            self.timeseries["DateTime"], errors="coerce"
                        ).fillna(0)
                        self.timeseries["DateTime"] = time_ints - MOWSECS_OFFSET
                        # Convert unix time to datetime
                        self.timeseries["DateTime"] = pd.to_datetime(
                            self.timeseries["DateTime"],
                            unit="s",
                            origin="unix",
                            utc=False,
                        )
                    self.timeseries.set_index("DateTime", inplace=True)
                return self

            
            def _format_timestamp(self, value) -> str:
                """Render a single timestamp back into its Hilltop text form.

                Mirrors ``construct_dataframe``'s parsing of the ``DateFormat``
                attribute: "Calendar" round-trips to an ISO-like string, and
                "mowsecs" round-trips to seconds-since-1940 as an integer string.
                """
                if pd.isna(value):
                    return ""
                timestamp = pd.Timestamp(value)
                if  self.date_format == "mowsecs":
                    return str(int(timestamp.timestamp()) + MOWSECS_OFFSET)
                # Default to the "Calendar" behaviour.
                return timestamp.strftime("%Y-%m-%dT%H:%M:%S")

            @staticmethod
            def _format_item_value(value, item: "ItemInfo") -> str:
                """Render a single data value back into its Hilltop text form.

                Reverses the divisor and type coercion applied for the given
                ``ItemFormat`` ("I", "F", "D" or "S") in ``construct_dataframe``.
                Note that "D"-formatted item columns are always rendered as
                Calendar-style strings, since the original text (Calendar vs.
                mowsecs) is not recoverable once both have been parsed into
                the same datetime value, and a mowsecs integer round-trips
                deterministically through ``construct_dataframe``'s fallback
                chain, unlike an ISO string, whose success depends on the
                first ``strptime``-style branch matching exactly.
                """
                if value is None or (isinstance(value, str) is False and pd.isna(value)):
                    return ""

                divisor = item.divisor or 1
                
                if item.item_format == "I":
                    return str(int(round(float(value) * divisor)))
                
                if item.item_format == "F":
                    scaled = float(value) * divisor
                    # `Format` (e.g. "####" or "####.##") is only a display
                    # hint, and in practice can understate a value's real
                    # precision (Hilltop servers have been observed to
                    # return e.g. "1024.53" for an item whose Format is
                    # "#.#", i.e. one decimal place). Treat it as a
                    # floor, not the true decimal count: widen as needed so
                    # the formatted text round-trips back to the same float.
                    
                    decimals = 0
                    
                    if item.format and "." in item.format:
                        decimals = len(item.format.split(".")[1])
                        
                    # Round off any floating-point noise introduced by the
                    # divisor multiplication before inspecting precision,
                    # so it doesn't get mistaken for genuine extra decimals.
                    natural = repr(round(scaled, 9))
                    if "." in natural and not natural.endswith(".0"):
                        decimals = max(decimals, len(natural.split(".")[1]))
                        
                    return f"{scaled:.{decimals}f}"
                
                if item.item_format == "D":
                    timestamp = pd.Timestamp(value)
                    return str(int(timestamp.timestamp()) + MOWSECS_OFFSET)
                # "S" (string) and anything unrecognised: pass through as text.
                return str(value)

            def to_xml_dict(self) -> dict:
                """Rebuild the raw ``xmltodict``-style dict for this <Data> element.

                This is the inverse of ``parse_data``/``construct_dataframe``: it
                turns ``self.timeseries`` back into a list of ``E`` row dicts, 
                undoing the column renaming, divisor scaling, and date
                formatting that were applied when the response was parsed.
                """
                result = {
                    "@DateFormat": self.date_format,
                    "@NumItems": str(self.num_items),
                }
                if self.timeseries.empty:
                    return result

                items_by_number = sorted(self.item_info, key=lambda i: i.item_number)
                is_datetime_indexed = self.timeseries.index.name == "DateTime"
                frame = (
                    self.timeseries.reset_index()
                    if is_datetime_indexed
                    else self.timeseries
                )

                rows = []
                for _, row in frame.iterrows():
                    entry = {}
                    if is_datetime_indexed:
                        entry["T"] = self._format_timestamp(row["DateTime"])
                    elif "D" in frame.columns:
                        entry["D"] = str(row["D"])
                    for item in items_by_number:
                        entry[f"I{item.item_number}"] = self._format_item_value(
                            row.get(item.item_name), item
                        )
                    rows.append(entry)
                result["E"] = rows
                return result
                                
        
        site_name: str = Field(alias="@SiteName")
        data_source: DataSource = Field(alias="DataSource")
        data: Data = Field(alias="Data", default_factory=list)
        tideda_site_number: str | None = Field(alias="TidedaSiteNumber", default=None)

        @model_validator(mode="before")
        def prepare_data_with_item_info(cls, values: dict) -> dict:
            """Inject them_info into Data before Data is constructed."""
            if "DataSource" in values and "Data" in values:
                data_source = values["DataSource"]
                data = values["Data"]

                # If Data is a dict, add item_info
                if isinstance(data, dict):
                    # Get item_info from DataSource
                    if isinstance(data_source, dict):
                        item_info = data_source.get("ItemInfo", [])
                    else:
                        item_info = getattr(data_source, "item_info", [])

                    # Add item_info to Data dict
                    data["item_info"] = item_info
                elif data is not None:
                    # If Data is already an object, set item_info directly
                    data.item_info = getattr(data_source, "item_info", [])
                    
            return values
    
        @model_validator(mode="after")
        def ensure_item_info_transferred(self) -> "self":
            """Ensure item_info is transferred to Data."""
            if self.data and self.data_source and self.data_source.item_info:
                if not self.data.item_info:
                    self.data.item_info = self.data_source.item_info
            return self

        def to_xml_dict(self) -> dict:
            """Rebuild the raw xmltodict-style dict for this <Measurement> element."""
            result = {
                "@SiteName": self.site_name,
                "DataSource": self.data_source.to_dict(),
                "Data": self.data.to_xml_dict(),
            }
            if self.tideda_site_number is not None:
                result["TidedaSiteNumber"] = self.tideda_site_number
            return result
    
    
    agency: str = Field(alias="Agency", default=None)
    measurements: list[Measurement] = Field(alias="Measurement", default_factory=list)
    error: str | None = Field(alias="Error", default=None)
    request: GetDataRequest | None = Field(default=None, exclude=True)

    @field_validator("measurements", mode="before")
    def validate_measurements(cls, value: dict | list) -> list[Measurement]:
        """Ensure measurements is a list, even when there is only one."""
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
        for measurement in self.measurements:
            frame = measurement.data.timeseries
            if not frame.empty:
                frame["Site"] = measurement.site_name
                frame["DataSource"] = measurement.data_source.name
                frames.append(frame)
        if len(frames) == 0:
            return pd.DataFrame()
        else:
            return pd.concat(frames, ignore_index=False)

    def to_xml(self, pretty: bool = True) -> str:
        """Serialize this response back into Hilltop GetData XML.

        This is the inverse of ``from_xml``. Note that it is a best-effort
        round-trip rather than a byte-for-byte one: numeric text is
        regenerated from the parsed values (using each item's ``Format``
        spec to decide decimal places), and datetime text is regenerated
        from the parsed timestamps according to the ``Data`` element's
        ``DateFormat``. Item-level "D"-formatted columns are always written
        back out as Calendar-style strings, since it's not possible to tell,
        after parsing, whether the original text was a Calendar-style string or a
        mowsecs integer.

        Parameters
        ----------
        pretty : bool
            Whether to indent the output XML. Defaults to True.

        Returns
        -------
        str
            The Hilltop GetData XML representation of this response.
        """
        root: dict = {}
        if self.agency is not None:
            root["Agency"] = self.agency
        if self.measurements:
            root["Measurement"] = [m.to_xml_dict() for m in self.measurements]

        return xmltodict.unparse({"Hilltop": root}, pretty=pretty)
        
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
