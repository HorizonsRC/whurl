"""GetData request schema.

This module defines the request model for retrieving measurement data
from Hilltop Server with various filtering and formatting options.
"""
from datetime import datetime
from typing import Literal, Any, Optional

import pandas as pd
from isodate import ISO8601Error, parse_datetime, parse_duration
from pydantic import Field, ValidationError, field_validator, model_validator

from whurl.exceptions import HilltopRequestError
from whurl.schemas.mixins import ModelReprMixin
from whurl.schemas.requests.base import BaseHilltopRequest
from whurl.utils import validate_datetime, validate_time_interval, validate_hilltop_interval_notation, DateTimeInput, DateTimeInputType


class GetDataRequest(BaseHilltopRequest):
    """Request parameters for Hilltop GetData endpoint.

    This request type retrieves measurement data from specific sites with
    options for time filtering, statistical processing, and output formatting.

    Parameters
    ----------
    request : str, default "GetData"
        Fixed request type for data retrieval queries.
    site : str, optional
        Name of the monitoring site to query.
    measurement : str, optional
        Name of the measurement type to retrieve.
    from_datetime : Optional[DateTimeInput]
        ???
    to_datetime : Optional[DateTimeInput]
        ???
    time_interval : str, optional
        Regular time interval for data aggregation.
    alignment : str, optional
        Time alignment for interval processing (e.g., "00:00").
    collection : str, optional
        Data collection name to filter by.
    method : str, optional
        Statistical method for data processing ("Interpolate", "Average",
        "Total", "Moving Average", "EP", "Extrema").
    interval : str, optional
        Time interval for statistical calculations.
    gap_tolerance : str, optional
        Maximum acceptable gap between data points.
    show_final: Literal["Yes"], optional
        ???
    date_only: Literal["Yes"], optional
        ???
    send_as: str, optional
        ???
    agency: str, optional
        ???
    format : Literal["Native", "WML2", "JSON"], optional
        Output format specification ("Native" or custom formats).
    ts_type: Literal["StdQualSeries", "Standard", "StdCheckSeries"], optional
        ???
    show_quality: Literal["Yes"], optional
        ???
    """

    request: str = Field(default="GetData", serialization_alias="Request")
    site: str | None = Field(default=None, serialization_alias="Site")
    measurement: str | None = Field(default=None, serialization_alias="Measurement")
    from_datetime: Any = Field(default=None, serialization_alias="From")
    to_datetime: Any = Field(default=None, serialization_alias="To")
    time_interval: str | Any | None = Field(default=None, serialization_alias="TimeInterval")
    alignment: str | None = Field(default=None, serialization_alias="Alignment")
    collection: str | None = Field(default=None, serialization_alias="Collection")
    method: (
        Literal["Interpolate", "Average", "Total", "Moving Average", "EP", "Extrema"]
        | None
    ) = Field(default=None, serialization_alias="Method")
    interval: str | None = Field(default=None, serialization_alias="Interval")
    gap_tolerance: str | None = Field(default=None, serialization_alias="GapTolerance")
    show_final: Literal["Yes"] | None = Field(
        default=None, serialization_alias="ShowFinal"
    )
    date_only: Literal["Yes"] | None = Field(
        default=None, serialization_alias="DateOnly"
    )
    send_as: str | None = Field(default=None, serialization_alias="SendAs")
    agency: str | None = Field(default=None, serialization_alias="Agency")
    format: Literal["Native", "WML2", "JSON"] | None = Field(
        default=None, serialization_alias="Format"
    )
    ts_type: Literal["StdQualSeries", "Standard", "StdCheckSeries"] | None = Field(
        default=None, serialization_alias="TSType"
    )
    show_quality: Literal["Yes"] | None = Field(
        default=None, serialization_alias="ShowQuality"
    )

    @field_validator("request", mode="before")
    def validate_request(cls, value):
        """Validate the request parameter."""
        if value != "GetData":
            raise HilltopRequestError("Request must be 'GetData'")
        return value

    @field_validator("from_datetime", mode="before")
    def validate_from_datetime(cls, from_value):
        """
        Validate datetime format.

        Parameters
        ----------
        from_value: str, Any, optional
            Valid inputs:
            - Strict ISO8601: "2026-08-20T14:30:00"
            - "Lazy" ISO8601 (space-separated): "2026-08-20 14:30:00"
            - pd.Timestamp objects
            - datetime.datetime objects
            - Numeric timestamps (int/float)
            - None (returns None)
            - "Data Start" (special string)

        Returns
        -------
        str: ISO8601 formatted datetime string (YYYY-MM-DDTHH:MM:SS)
        None: if input is None
        "Data Start": if input is the special string
            
        """
        try:
            return validate_datetime(from_value, "from_datetime", special_cases=["Data Start"])
        except (ValueError, TypeError) as e:
            raise HilltopRequestError(str(e))

    @field_validator("to_datetime", mode="before")
    def validate_to_datetime(cls, to_value):
        """Validate datetime format."""
        try:
            return validate_datetime(to_value, "to_datetime", special_cases=["Data End", "now"])
        except (ValueError, TypeError) as e:
            raise HilltopRequestError(str(e))
            
    @field_validator("time_interval", mode="before")
    def validate_time_interval(cls, value):
        """Validate ISO8601 Time Interval format."""

        try:
            return validate_time_interval(value)
        except (ValueError, TypeError) as e:
            raise HilltopRequestError(str(e))
    
    @field_validator("alignment", mode="before")
    def validate_alignment(cls, value):
        """
        Validate the alignment parameter.

        From what I can tell this can either be a time of day, or a Hilltop interval.
        """
        if value is None:
            return None
        try:
            # Test to see if it is a time of day (Time only, no date)
            time = pd.to_datetime(value)
            if time.date() != datetime.now().date():
                raise HilltopRequestError(
                    "Alignment must be a time of day (e.g. '12:00:00') or a "
                    "Hilltop interval  (e.g '1 month'). You entered "
                    f"'{value}' which is not a valid time of day."
                )
        except ValueError:
            # If it fails, check if it's a Hilltop interval
            try:
                validate_hilltop_interval_notation(value)
            except ValueError as e:
                raise HilltopRequestError(str(e))

        return value

    @model_validator(mode="after")
    def check_time_interval(self) -> "self":
        """Check if time_interval is valid."""
        if self.alignment is not None and self.time_interval is None:
            raise HilltopRequestError(
                "TimeInterval must be specified when Alignment is specified."
            )
        return self

    @field_validator("method", mode="before")
    def validate_method(cls, value):
        """Validate the method parameter."""
        if value is None:
            return None
        if value not in [
            "Interpolate",
            "Average",
            "Total",
            "Moving Average",
            "EP",
            "Extrema",
        ]:
            raise HilltopRequestError(
                "Invalid method. Method must be one of: 'Interpolate', 'Average', 'Total', "
                "'Moving Average', 'EP', 'Extrema'."
            )
        return value

    @field_validator("interval", mode="before")
    def validate_interval(cls, value):
        """Validate the interval parameter."""
        if value is None:
            return None
        validate_hilltop_interval_notation(value)
        return value

    @field_validator("gap_tolerance", mode="before")
    def validate_gap_tolerance(cls, value):
        """Validate the gap_tolerance parameter."""
        if value is None:
            return None
        validate_hilltop_interval_notation(value)
        return value

    @model_validator(mode="after")
    def check_statistics(self) -> "self":
        """Check that the 'Method' and 'Interval' parameters are valid."""
        if self.interval is not None and self.method is None:
            raise HilltopRequestError(
                "Method required. Method must be specified when Interval is specified."
            )
        if self.gap_tolerance is not None and self.method is None:
            raise HilltopRequestError(
                "Method required. Method must be specified when GapTolerance is specified."
            )
        if self.show_final is not None and self.method is None:
            raise HilltopRequestError(
                "Method required. Method must be specified when ShowFinal is specified."
            )
        if self.send_as is not None and self.method is None:
            raise HilltopRequestError(
                "Method required. Method must be specified when SendAs is specified."
            )
        if self.method in ["Average", "Total", "Moving Average", "Extrema"]:
            if self.interval is None:
                raise HilltopRequestError(
                    "Interval Required. Interval must be specified when Method is 'Average', "
                    "'Total', 'Moving Average', or 'Extrema'."
                )
        return self

    @model_validator(mode="after")
    def check_datetimes(self) -> "self":
        """Check if from and to datetime are valid."""
        if self.from_datetime is not None and self.to_datetime is not None:
            if (
                self.from_datetime == "Data Start"
                or self.to_datetime == "Data End"
                or self.to_datetime == "now"
            ):
                return self
            else:
                try:
                    from_dt = parse_datetime(self.from_datetime)
                    to_dt = parse_datetime(self.to_datetime)
                    if from_dt > to_dt:
                        raise HilltopRequestError(
                            "From datetime must be before To datetime."
                        )
                except ISO8601Error as e:
                    raise HilltopRequestError(f"Invalid datetime format: {e}") from e

        return self
