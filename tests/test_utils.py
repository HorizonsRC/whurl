import pytest
import warnings
from datetime import datetime, timezone, timedelta
import pandas as pd
from whurl.utils import validate_datetime, NZST
from whurl.exceptions import TimezoneConversionWarning

class TestValidateDatetime:
    """Test suite for datetime validation."""

    # Test data
    testdata = [
        # ISO8601 strict format
        ("2026-08-20T14:30:00", "2026-08-20T14:30:00"),
        ("2026-08-20T09:05:12", "2026-08-20T09:05:12"),
        ("2026-12-31T23:59:59", "2026-12-31T23:59:59"),
        
        # Space-separated format (pandas)
        ("2026-08-20 14:30:00", "2026-08-20T14:30:00"),
        ("2026-08-20 09:05:12", "2026-08-20T09:05:12"),
        
        # Date-only format (assumes midnight)
        ("2026-08-20", "2026-08-20T00:00:00"),
        ("2026-12-31", "2026-12-31T00:00:00"),
        
        # Various separator formats
        ("2026/08/20 14:30:00", "2026-08-20T14:30:00"),
        
        # Special strings
        (None, None),
        ("Data Start", "Data Start"),
        ("Data start", "Data Start"),
        ("data start", "Data Start"),
        ("DATA START", "Data Start"),
        ("Data End", "Data End"),
        ("Data end", "Data End"),
        ("data end", "Data End"),
        ("DATA END", "Data End"),
        ("now", "now"),
        ("Now", "now"),
        ("NOW", "now"),
        
        # pandas Timestamp
        (pd.Timestamp("2026-08-20 14:30:00"), "2026-08-20T14:30:00"),
        (pd.Timestamp("2026-12-31 23:59:59"), "2026-12-31T23:59:59"),
        
        # datetime objects
        (datetime(2026, 8, 20, 14, 30, 0), "2026-08-20T14:30:00"),
        (datetime(2026, 12, 31, 23, 59, 59), "2026-12-31T23:59:59"),
        
        
        
        # Numeric timestamps
        (1787236200, "2026-08-20T14:30:00"),  # Unix timestamp
        (1787236200.0, "2026-08-20T14:30:00"),  # Float timestamp   
    ]
    
    @pytest.mark.unit
    @pytest.mark.parametrize("input_value,expected", testdata)
    def test_valid_inputs(self, input_value, expected):
        """Test various valid datetime inputs."""
        result = validate_datetime(
            input_value,
            special_cases=["Data Start", "Data End", "now"]
        )
        assert result == expected


class TestTimezoneWarnings:
    """Test timezone conversion warnings."""
    
    def test_warning_on_utc_conversion(self):
        """Test that UTC conversion raises a warning."""
        dt = datetime(2026, 8, 20, 14, 30, 0, tzinfo=timezone.utc)
        
        with pytest.warns(TimezoneConversionWarning) as record:
            result = validate_datetime(dt)
        
        assert "UTC" in str(record[0].message)
        assert "converted to NZST" in str(record[0].message)
        assert result == "2026-08-21T02:30:00"  # NZST is UTC+12
    
    def test_warning_on_other_timezone(self):
        """Test that other timezone conversion raises a warning."""
        dt = datetime(2026, 8, 20, 14, 30, 0, tzinfo=timezone(timedelta(hours=-4)))
        
        with pytest.warns(TimezoneConversionWarning):
            result = validate_datetime(dt)
        
        assert result == "2026-08-21T06:30:00"  # -04:00 to NZST (+12)
    
    def test_no_warning_on_naive(self):
        """Test that naive datetime doesn't raise a warning."""
        dt = datetime(2026, 8, 20, 14, 30, 0)
        
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            result = validate_datetime(dt)
        
        assert result == "2026-08-20T14:30:00"
    
        
    def test_warning_on_pandas_timestamp_utc(self):
        """Test that pandas UTC Timestamp conversion raises a warning."""
        ts = pd.Timestamp("2026-08-20T14:30:00", tz="UTC")
        
        with pytest.warns(TimezoneConversionWarning):
            result = validate_datetime(ts)
        
        assert result == "2026-08-21T02:30:00"

    def test_no_warning_on_nz_timezone_pandas(self):
        """Test that NZ timezone doesn't raise a warning."""
        ts = pd.Timestamp("2026-08-20T14:30:00")
        
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            result = validate_datetime(ts)
        
        assert result == "2026-08-20T14:30:00"
        
    def test_no_warning_on_nz_timezone_datetime(self):
        """Test that NZ timezone doesn't raise a warning."""
        dt = datetime(2026, 8, 20, 14, 30, 0, tzinfo=NZST)
        
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            result = validate_datetime(dt)
        
        assert result == "2026-08-20T14:30:00"
        
import pytest
from whurl.exceptions import HilltopRequestError
from whurl.utils import validate_hilltop_interval_notation


class TestValidateHilltopIntervalNotation:
    """Test suite for validate_hilltop_interval_notation function."""

    @pytest.mark.parametrize("input_value,expected", [
        # Seconds
        ("10 seconds", "10 seconds"),
        ("10 second", "10 second"),
        ("1seconds", "1seconds"),
        ("1second", "1second"),
        ("10.1 s", "10.1 s"),
        ("25.5s", "25.5s"),
        
        # Minutes
        ("100 minutes", "100 minutes"),
        ("100 minute", "100 minute"),
        ("1.0minutes", "1.0minutes"),
        ("1.0minute", "1.0minute"),
        ("4340 m", "4340 m"),
        ("10.4m", "10.4m"),
        
        # Hours
        ("6 hours", "6 hours"),
        ("6 hour", "6 hour"),
        ("999hours", "999hours"),
        ("999hour", "999hour"),
        ("3.4 h", "3.4 h"),
        ("2000.1h", "2000.1h"),
        
        # Days
        ("7 days", "7 days"),
        ("7 day", "7 day"),
        ("100000days", "100000days"),
        ("100000day", "100000day"),
        ("10 d", "10 d"),
        ("10d", "10d"),
        
        # Weeks
        ("52 weeks", "52 weeks"),
        ("52 week", "52 week"),
        ("0.4weeks", "0.4weeks"),
        ("0.4week", "0.4week"),
        ("1 w", "1 w"),
        ("7w", "7w"),
        
        # Months
        ("010 months", "010 months"),
        ("10 month", "10 month"),
        ("10months", "10months"),
        (".10month", ".10month"),
        ("10 mo", "10 mo"),
        ("10mo", "10mo"),
        
        # Years
        ("10 years", "10 years"),
        ("10 year", "10 year"),
        (".5years", ".5years"),
        ("10year", "10year"),
        ("10 y", "10 y"),
        ("10y", "10y"),
    ])
    @pytest.mark.unit
    def test_valid_inputs(self, input_value, expected):
        """Test various valid interval notation inputs."""
        assert validate_hilltop_interval_notation(input_value) == expected

    @pytest.mark.parametrize("input_value", [
        None,
        "",
        "invalid",
        "10,000 seconds",
        "15parsecs",
        "15 parsecs",
    ])
    @pytest.mark.unit
    def test_invalid_inputs(self, input_value):
        """Test various invalid interval notation inputs."""
        with pytest.raises(ValueError):
            validate_hilltop_interval_notation(input_value)
