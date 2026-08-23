"""WHURL utilities module.

This module contains utility functions for validating and processing
Hilltop-specific data formats and request parameters.
"""

import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Union, Any
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema
import pandas as pd
from isodate import ISO8601Error, parse_datetime, parse_duration
import warnings
from whurl.exceptions import TimezoneConversionWarning


# Define NZ timezones
NZST = timezone(timedelta(hours=12))  # UTC+12

DateTimeInputType = Union[str, pd.Timestamp, datetime, int, float, None]

FROM_SPECIAL_KEYWORDS = ["Data Start"]
TO_SPECIAL_KEYWORDS = ["Data End", "now"]

class DateTimeInput:
    """
    Type for datetime inputs that can be normalized to ISO8601.

    This object is structured specifically so that Pydantic can validate it as an input datatype
    
    Accepts strings (ISO8601, space-separated, or date-only), pandas Timestamps,
    datetime objects, numeric timestamps, None, or the special string "Data Start".
    
    Examples
    --------
    >>> from whurl.utils.datetime_utils import validate_datetime
    >>> dt = DateTimeInput()
    >>> validate_datetime("2026-08-20T14:30:00")
    '2026-08-20T14:30:00'
    >>> validate_datetime(pd.Timestamp("2026-08-20 14:30:00"))
    '2026-08-20T14:30:00'
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        """Generate Pydantic core schema for DateTimeInput type."""

        # Define valid input types
        valid_types = (
            str,
            pd.Timestamp,
            datetime,
            int,
            float,
            type(None)
        )

        # Create union schema of all acceptable types
        return core_schema.union_schema([
            core_schema.str_schema(),
            core_schema.is_instance_schema(pd.Timestamp),
            core_schema.is_instance_schema(datetime),
            core_schema.int_schema(),
            core_schema.float_schema(),
            core_schema.none_schema(),
        ])

def validate_datetime(
    value: Any,
    field_name: str = "datetime",
    special_cases: list = []
) -> Optional[str]:
    """
    Validate various datetime inputs to ISO8601 string format

    This function accepts multiple datetime formats and consistently returns a string
    in strict ISO8601 format (YYYY-MM-DDTHH:MM:SS) suitable for Hilltop Server API requests.

    Parameters
    ----------
    value: Input datetime value (string, pandas Timestamp, datetime.datetime, int, float, or None)
    field_name: Name of the pydantic field being validated (for error messages).

    Returns
    -------
    Optional[str]: ISO8601 formatted string, None if input is None, or special strings like "Data Start"
    
    """

    # Case 1: None is valid
    if value is None:
        return None

    # Case 2: Special strings that should pass through
    special_cases_lower = [s.lower() for s in special_cases]
    all_special_cases_lower = [s.lower() for s in FROM_SPECIAL_KEYWORDS + TO_SPECIAL_KEYWORDS]

    if isinstance(value, str) and value.lower() in special_cases_lower:
        # Find the index of the match
        idx = special_cases_lower.index(value.lower())
        return special_cases[idx]
    elif isinstance(value, str) and value.lower() in all_special_cases_lower:
        # If it's not in the special cases, but it is a special keyword in general...
        raise ValueError(
            f"Special keyword '{value}' cannot be used in the '{field_name}' position."

        )

        

    # Case 3: String input - accept multiple formats
    if isinstance(value, str):
        return _validate_string_datetime(value, field_name)

    # Case 4: pd.Timestamp - convert to ISO8601
    if isinstance(value, pd.Timestamp):
        return _validate_pandas_timestamp(value, field_name)

    # Case 5: datetime.datetime - convert to ISO8601
    if isinstance(value, datetime):
        return _validate_datetime_object(value, field_name)

    # Case 6: int/float timestamps - convert to ISO8601
    if isinstance(value, (int, float)):
        return _validate_numeric_timestamp(value, field_name)

    # Case 7: Everythign else is invalid
    raise TypeError(
        f"{field_name} must be a string (ISO8601 format), pd.Timestamp, "
        f"datetime.datetime, numeric timestamp, or None. "
        f"Got {type(value).__name__}: {value}"
    )


def _validate_string_datetime(value: str, field_name: str) -> str:
    """Parse string datetime and validate to ISO8601."""
    try:
        # Try strict ISO8601 parsing first
        dt = parse_datetime(value)
        dt = _to_nzst(dt)
        return _format_iso8601(dt)
    except ISO8601Error:
        # Fall back to pandas for more flexible parsing
        try: 
            dt = pd.to_datetime(value)
            if pd.isna(dt):
                raise ValueError(f"Invalid datetime string: {value}")
            dt = _to_nzst(dt)
            return _format_iso8601(dt)
        except Exception as e:
            raise ValueError(
                f"Error parsing {field_name} value: '{value}'. "
                "Datetime must be in the format 'yyyy-mm-ddTHH:MM:SS', "
                "'yyyy-mm-dd HH:MM:SS', or 'yyyy-mm-dd'. "
                f"Error: {e}"
            )
    

def _validate_pandas_timestamp(value: pd.Timestamp, field_name: str) -> str:
    """Convert pandas Timestamp to ISO8601."""
    if pd.isna(value):
        raise ValueError(f"{field_name} cannot be NaT (pandas Not a Time object)")
    dt = _to_nzst(value)
    return _format_iso8601(dt)


def _validate_datetime_object(value: datetime, field_name: str) -> str:
    """Convert datetime.datetime object to ISO8601."""
    dt = _to_nzst(value)
    return _format_iso8601(dt)


def _validate_numeric_timestamp(value: Union[int, float], field_name: str) -> str:
    """Convert numeric timestamp to ISO8601."""
    try:
        # Assume seconds since epoch
        dt = pd.to_datetime(value, unit='s', utc=False)
        if pd.isna(dt):
            raise ValueError(f"Invalid numeric timestamp: {value}")
        return _format_iso8601(dt.to_pydatetime())
    except Exception as e:
        raise ValueError(f"Invalid numeric timestamp for {field_name}: {e}")


def _format_iso8601(dt: datetime) -> str:
    """Format datetime to strict ISO8601 without timezone."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def validate_time_interval(value: Optional[str]) -> Optional[str]:
    """
    Validate a time interval value for Hilltop Server API.

    Accepts ISO8601 intervals (start/end, start/duration, duration/end),
    standalone durations, or special keywords ("Data Start", "Data End", "now").

    Parameters
    ----------
    value: Optional[str]
        Time interval string to validate.

    Returns
    -------
    Optional[str]
        Valid time interval string, or None if input is None.

    Raises
    ------
    ValueError
        If the time in terval format is invalid.

    Examples
    --------
    >>> validate_time_interval("2026-08-20T14:30:00/2026-08-20T15:30:00")
    '2026-08-20T14:30:00/2026-08-20T15:30:00'
    >>> validate_time_interval("P1D/Data End")
    'P1D/Data End'
    >>> validate_time_interval("Data Start/PT2H")
    'Data Start/PT2H'
    """

    if value is None:
        return None

    if not isinstance(value, str):
        raise TypeError(f"Time interval must be a string, got {type(value).__name__}")

    # Special strings that should pass through
    special_cases = ["Data Start", "Data End", "now"]
    special_cases_lower = [s.lower() for s in special_cases]
    
    if isinstance(value, str) and value.lower() in special_cases_lower:
        # Find the index of the match
        idx = special_cases_lower.index(value.lower())
        return special_cases[idx]
    
    # Standalone duration
    if _is_valid_duration(value):
        return value

    # Interval with "/" separator
    if "/" in value:
        print("Validating Interval!")
        return _validate_interval(value)

    raise ValueError(
        f"Invalid time interval format: '{value}'. "
        "Expected ISO8601 interval (start/end, start/duration, duration/end), "
        "standalone duration, or special keyword ('Data Start', 'Data End', 'now')."
    )


def _validate_interval(value: str) -> str:
    """Validate an ISO8601 time interval."""
    part1, part2 = value.split("/", 1)

    # Parse and validate each part
    part1_validated = _validate_interval_part(part1, "start")
    part2_validated = _validate_interval_part(part2, "end")

    # Validate ordering if both parts are datetimes
    if _is_datetime(part1) and _is_datetime(part2):
        dt1 = parse_datetime(part1)
        dt2 = parse_datetime(part2)
        if dt1 > dt2:
            raise ValueError(
                f"Start datetime '{part1}' must be before end datetime '{part2}'"
            )

    return f"{part1_validated}/{part2_validated}"


def _validate_interval_part(part: str, position: str) -> str:
    """Validate a single part of a time interval.

    Parameters
    __________
    part: str
        The interval part to validate
    position: str
        Whether this is the "start" or "end" part.

    Returns
    -------
    str
        Validated interval part.

    Raises
    ------
    ValueError
        If the part is invalid
    """
    # Special keywords
    from_kw_lower = [kw.lower() for kw in FROM_SPECIAL_KEYWORDS]
    to_kw_lower = [kw.lower() for kw in TO_SPECIAL_KEYWORDS]
    if position == "start":
        if part.lower() in from_kw_lower:
            return part
        elif part.lower() in to_kw_lower:
            raise ValueError(
                f"Invalid {position} part '{part}'. "
                f"'{part}' cannot be used as the {position} keyword. "
                f"Available {position} keywords: {FROM_SPECIAL_KEYWORDS}."
            )
    if position == "end":
        if part.lower() in to_kw_lower:
            return part
        elif part.lower() in from_kw_lower:
            raise ValueError(
                f"Invalid {position} part '{part}'. "
                f"'{part}' cannot be used as the {position} keyword. "
                f"Available {position} keywords: {TO_SPECIAL_KEYWORDS}."
            )

    # Check if it's a valid duration
    if _is_valid_duration(part):
        return part

    # Check if it's a valid datetime
    if _is_valid_datetime(part):
        # Validate datetime to strict ISO8601
        valid = validate_datetime(part)
        if valid is None: # Should never happen for valid datetime
            raise ValueError(f"Failed to validate datetime: {part}")
        return valid

    raise ValueError(
        f"Invalid {position} part '{part}'. "
        "Expected ISO8601 datetime, ISO8601 duration, or special keyword "
        "('Data Start', 'Data End', 'now')."
    )


def _is_valid_datetime(value: str) -> bool:
    """Check if string is a valid ISO8601 datetime."""
    try:
        parse_datetime(value)
        return True
    except ISO8601Error:
        return False


def _is_valid_duration(value: str) -> bool:
    """Check if string is a valid ISO8601 duration."""
    try:
        parse_duration(value)
        return True
    except ISO8601Error:
        return False


def _is_datetime(value: str) -> bool:
    """Check if string is a datetime (not a special keyword or duration)."""
    if value in ("Data Start", "Data End", "now"):
        return False
    if _is_valid_duration(value):
        return False
    return _is_valid_datetime(value)
    

def _to_nzst(value: Union[pd.Timestamp, datetime]) -> datetime:
    """Convert timestamp to naive datetime in NZST"""
    if isinstance(value, pd.Timestamp):
        if value.tz is not None:
            # Check if it's already in NZ timezone
            is_nz = str(value.utcoffset()) == "12:00:00"

            # Convert to NZ timezone
            converted = value.tz_convert(NZST)

            # Make naive
            converted = converted.tz_localize(None)

            # Warn if it wasn't already NZST
            if not is_nz:
                warnings.warn(
                    f"Timezone '{value.tz}' converted to NZST. "
                    f"Original time: {value}, NZST time: {converted}",
                    TimezoneConversionWarning,
                    stacklevel=3  #Stack level to point to user's code
                )
            return converted.to_pydatetime()
        # If naive, assume NZST already
        return value.to_pydatetime()
    
    # datetime object
    if value.tzinfo is not None:
        is_nz = str(value.utcoffset()) == "12:00:00"
        # Convert to NZ timezone
        converted = value.astimezone(NZST)

        if not is_nz:
            warnings.warn(
                f"Timezone '{value.tzinfo}' converted to NZST. "
                f"Original: {value}, NZST: {converted}",
                TimezoneConversionWarning,
                stacklevel=3
            )
        return converted.replace(tzinfo=None)
    # If naive, assume NZST already
    return value

def validate_hilltop_interval_notation(value: str) -> str:
    """Validate Hilltop interval notation format.

    Validates time interval strings according to Hilltop Server requirements.
    Accepts formats like "2.5 minutes", "1 hour", or just "30" (for seconds).

    From the Hilltop documentation: Set an interval by entering a value and
    its units with a space between the number and units. Valid units are
    seconds, minutes, hours, days, months and years. The default units are
    seconds, so units are not required if your interval is in seconds.

    Parameters
    ----------
    value : str
        The interval notation string to validate.

    Returns
    -------
    str
        The validated interval notation string.

    Raises
    ------
    HilltopRequestError
        If the interval notation format is invalid or uses unsupported units.

    Examples
    --------
    >>> validate_hilltop_interval_notation("1 hour")
    '1 hour'
    >>> validate_hilltop_interval_notation("30")
    '30'
    >>> validate_hilltop_interval_notation("2.5 minutes")
    '2.5 minutes'
    """
    if isinstance(value, str):
        # Regex all leading numbers and decimal points
        matches = re.findall(r"(\d+\.?\d*)\s?([a-zA-Z]+)?", value)
        if matches:
            parts = matches[0]
            number = parts[0]
            if len(parts) > 1:
                units = parts[1]
            else:
                units = None

            # Check if the first part is a number
            if not str(number).replace(".", "", 1).isdigit():
                raise ValueError(
                    f"Invalid interval format: '{value}'. "
                    "Expected format: '<time interval (in secs)> OR "
                    "<time interval> <units>'."
                )

            if units is not None and units not in [
                "seconds",
                "second",
                "minutes",
                "minute",
                "hours",
                "hour",
                "days",
                "day",
                "weeks",
                "week",
                "months",
                "month",
                "years",
                "year",
                "s",
                "m",
                "h",
                "d",
                "w",
                "mo",
                "y",
            ]:
                raise ValueError(
                    f"Invalid interval units: '{units}'. "
                    "Valid units are: seconds, minutes, hours, days, "
                    "weeks, months, years."
                )
        else:
            raise ValueError(
                f"Invalid interval format: '{value}'. "
                "Expected format: '<time interval (in secs)> OR "
                "<time interval> <units>'."
            )
    elif not isinstance(value, (int, float)):
        raise ValueError(
            f"Invalid interval format: '{value}'. "
            "Expected format: '<time interval (in secs)> OR "
            "<time interval> <units>'."
        )

    return value


def sanitise_xml_attributes(xml_str: str) -> str:
    """Sanitise XML attributes by escaping special characters.

    Escapes special XML characters (&, <, >, ") in attribute values to prevent
    XML parsing errors and ensure well-formed XML documents.

    Parameters
    ----------
    xml_str : str
        The XML string containing attributes to sanitise.

    Returns
    -------
    str
        The XML string with sanitised attribute values.

    Examples
    --------
    >>> sanitise_xml_attributes('name="value with & < > characters"')
    'name="value with &amp; &lt; &gt; characters"'
    """
    clean = re.sub(
        r'="([^"]*.*)"',
        lambda m: '="'
        + (
            m.group(1)
            .replace('"', "&quot;")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        + '"',
        xml_str,
    )
    return clean
