"""WHURL utils module."""

import re

from whurl.exceptions import HilltopRequestError


def validate_hilltop_interval_notation(value: str) -> str:
    """
    Validate the Hilltop interval notation.

    From the Hilltop docs:

    Set an interval by entering a value and its units into the text field with a
    space between the number and its units, for example 2.5 minutes.
    Valid units are seconds, minutes, hours, days, months and years.
    The default units are seconds so units are not required if your interval is in
    seconds.

    You don't have to type all the keyword, for example 1 w will retrieve one value
    per week.

    An interval of zero retrieves the filed values at whatever time steps were used.

    Hydro uses a fixed interval for months and years based on a solar year. One
    solar year is 365.25 days and a solar month is one twelfth of a solar year.

    <time interval (in secs)> OR <time interval><units>>

    HOWEVER, it seems that it also works without a space

    Args
    ----
        value (str): The interval notation to validate.

    Raises
    ------
        HilltopRequestError: If the interval notation is invalid.

    Returns
    -------
        str: The validated interval notation.
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
    """Sanitise XML attributes by escaping special characters."""
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
