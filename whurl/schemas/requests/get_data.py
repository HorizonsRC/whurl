"""GetData request schema.

This module defines the request model for retrieving measurement data
from Hilltop Server with various filtering and formatting options.
"""

from datetime import datetime
from typing import Literal

import pandas as pd
from isodate import ISO8601Error, parse_datetime, parse_duration
from pydantic import Field, ValidationError, field_validator, model_validator

from whurl.exceptions import HilltopRequestError
from whurl.schemas.mixins import ModelReprMixin
from whurl.schemas.requests.base import BaseHilltopRequest
from whurl.utils import validate_hilltop_interval_notation


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
    from_datetime : str, optional
        Start datetime for data retrieval (ISO 8601 format).
    to_datetime : str, optional
        End datetime for data retrieval (ISO 8601 format).
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
    format : str, optional
        Output format specification ("Native" or custom formats).
    """

    request: str = Field(default="GetData", serialization_alias="Request")
    site: str | None = Field(default=None, serialization_alias="Site")
    measurement: str | None = Field(default=None, serialization_alias="Measurement")
    from_datetime: str | None = Field(default=None, serialization_alias="From")
    to_datetime: str | None = Field(default=None, serialization_alias="To")
    time_interval: str | None = Field(default=None, serialization_alias="TimeInterval")
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
    ts_type: Literal["StdQualSeries"] | None = Field(
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
        """Validate datetime format."""
        try:
            if from_value != "Data Start":
                parse_datetime(from_value)
        except ISO8601Error:
            raise HilltopRequestError(
                f"Error parsing 'to_datetime' value: '{from_value}'. "
                "Datetime must be in the format 'yyyy-mm-ddTHH:MM:SS'. "
                "See ISO8601 documentation for more details."
            )
        return from_value

    @field_validator("to_datetime", mode="before")
    def validate_to_datetime(cls, to_value):
        """Validate datetime format."""
        try:
            if to_value not in ["Data End", "now"]:
                parse_datetime(to_value)
        except ISO8601Error or ValueError as e:
            raise HilltopRequestError(
                f"Error parsing 'to_datetime' value: '{to_value}'. "
                "Datetime must be in the format 'yyyy-mm-ddTHH:MM:SS'. "
                "See ISO8601 documentation for more details."
            ) from e
        return to_value

    @field_validator("time_interval", mode="before")
    def validate_time_interval(cls, value):
        """Validate ISO8601 Time Interval format."""
        if value is None:
            return None

        if not isinstance(value, str):
            raise HilltopRequestError(
                f"Invalid time interval format: '{value}'.\n"
                "Expected ISO8601 interval/duration or Hilltop special keywords "
                "('Data Start', 'Data End', 'now')."
            )

        # Check for interval (start/end or start/duration or duration/end)
        if "/" in value:
            part1, part2 = value.split("/", 1)

            # Case 1: Both parts are datetimes or keywords
            try:
                part1_dt = None
                part2_dt = None
                if part1 != "Data Start":
                    part1_dt = parse_datetime(part1)
                if part2 not in ["Data End", "now"]:
                    part2_dt = parse_datetime(part2)
                if part1_dt and part2_dt:
                    if part1_dt > part2_dt:
                        raise HilltopRequestError(
                            "From datetime must be before To datetime."
                        )
                return value  # Both parts are valid ISO8601 datetimes or keywords
            except ISO8601Error as e:
                pass  # Either parts might be a valid duration
            except ValueError as e:
                raise HilltopRequestError(
                    f"Invalid time interval format: '{value}'.\n"
                    "Expected ISO8601 interval/duration or Hilltop special keywords "
                    "('Data Start', 'Data End', 'now')."
                ) from e

            # Case 2: Part1 is duration, Part2 is datetime/keyword
            try:
                parse_duration(part1)
                if part2 in ["Data End", "now"] or parse_datetime(part2):
                    return value
            except ISO8601Error as e:
                pass  # Could be other way around
            except ValueError as e:
                raise HilltopRequestError(
                    f"Invalid time interval format: '{value}'.\n"
                    "Expected ISO8601 interval/duration or Hilltop special keywords "
                    "('Data Start', 'Data End', 'now')."
                ) from e

            # Case 3: Part1 is datetime/keyword, Part2 is duration
            try:
                if part1 == "Data Start" or parse_datetime(part1):
                    parse_duration(part2)
                    return value
                else:
                    raise HilltopRequestError(
                        f"Invalid time interval format: '{value}'.\n"
                        "Expected ISO8601 interval/duration or Hilltop special keywords"
                        " ('Data Start', 'Data End', 'now')."
                    )
            except ISO8601Error as e:
                pass
            except ValueError as e:
                raise HilltopRequestError(
                    f"Invalid time interval format: '{value}'.\n"
                    "Expected ISO8601 interval/duration or Hilltop special keywords "
                    "('Data Start', 'Data End', 'now')."
                ) from e

        # Case 4: Standalone duration
        try:
            parse_duration(value)
            return value
        except ISO8601Error as e:
            pass
        except ValueError as e:
            raise HilltopRequestError(
                f"Invalid time interval format: '{value}'.\n"
                "Expected ISO8601 interval/duration or Hilltop special keywords "
                "('Data Start', 'Data End', 'now')."
            ) from e

        raise HilltopRequestError(
            f"Invalid time interval format: '{value}'.\n"
            "Expected ISO8601 interval/duration or Hilltop special keywords "
            "('Data Start', 'Data End', 'now')."
        )

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
            validate_hilltop_interval_notation(value)  # Raises HilltopRequestError

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
                "Method must be one of: 'Interpolate', 'Average', 'Total', "
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
                "Method must be specified when Interval is specified."
            )
        if self.gap_tolerance is not None and self.method is None:
            raise HilltopRequestError(
                "Method must be specified when GapTolerance is specified."
            )
        if self.show_final is not None and self.method is None:
            raise HilltopRequestError(
                "Method must be specified when ShowFinal is specified."
            )
        if self.send_as is not None and self.method is None:
            raise HilltopRequestError(
                "Method must be specified when SendAs is specified."
            )
        if self.method in ["Average", "Total", "Moving Average", "Extrema"]:
            if self.interval is None:
                raise HilltopRequestError(
                    "Interval must be specified when Method is 'Average', "
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
