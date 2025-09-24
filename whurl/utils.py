"""WHURL utilities module.

This module contains utility functions for validating and processing
Hilltop-specific data formats and request parameters.
"""

import re

from whurl.exceptions import HilltopRequestError


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
                raise HilltopRequestError(
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
                raise HilltopRequestError(
                    f"Invalid interval units: '{units}'. "
                    "Valid units are: seconds, minutes, hours, days, "
                    "weeks, months, years."
                )
        else:
            raise HilltopRequestError(
                f"Invalid interval format: '{value}'. "
                "Expected format: '<time interval (in secs)> OR "
                "<time interval> <units>'."
            )
    elif not isinstance(value, (int, float)):
        raise HilltopRequestError(
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
