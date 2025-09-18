import pytest


@pytest.mark.unit
def test_validate_hilltop_interval_notation():
    """Test validate_hilltop_interval_notation function."""
    from hurl.exceptions import HilltopRequestError
    from hurl.utils import validate_hilltop_interval_notation

    # Valid cases
    assert validate_hilltop_interval_notation("10 seconds") == "10 seconds"
    assert validate_hilltop_interval_notation("10 second") == "10 second"
    assert validate_hilltop_interval_notation("1seconds") == "1seconds"
    assert validate_hilltop_interval_notation("1second") == "1second"
    assert validate_hilltop_interval_notation("10.1 s") == "10.1 s"
    assert validate_hilltop_interval_notation("25.5s") == "25.5s"

    assert validate_hilltop_interval_notation("100 minutes") == "100 minutes"
    assert validate_hilltop_interval_notation("100 minute") == "100 minute"
    assert validate_hilltop_interval_notation("1.0minutes") == "1.0minutes"
    assert validate_hilltop_interval_notation("1.0minute") == "1.0minute"
    assert validate_hilltop_interval_notation("4340 m") == "4340 m"
    assert validate_hilltop_interval_notation("10.4m") == "10.4m"

    assert validate_hilltop_interval_notation("6 hours") == "6 hours"
    assert validate_hilltop_interval_notation("6 hours") == "6 hours"
    assert validate_hilltop_interval_notation("999hours") == "999hours"
    assert validate_hilltop_interval_notation("999hour") == "999hour"
    assert validate_hilltop_interval_notation("3.4 h") == "3.4 h"
    assert validate_hilltop_interval_notation("2000.1h") == "2000.1h"

    assert validate_hilltop_interval_notation("7 days") == "7 days"
    assert validate_hilltop_interval_notation("7 day") == "7 day"
    assert validate_hilltop_interval_notation("100000days") == "100000days"
    assert validate_hilltop_interval_notation("100000day") == "100000day"
    assert validate_hilltop_interval_notation("10 d") == "10 d"
    assert validate_hilltop_interval_notation("10d") == "10d"

    assert validate_hilltop_interval_notation("52 weeks") == "52 weeks"
    assert validate_hilltop_interval_notation("52 week") == "52 week"
    assert validate_hilltop_interval_notation("0.4weeks") == "0.4weeks"
    assert validate_hilltop_interval_notation("0.4week") == "0.4week"
    assert validate_hilltop_interval_notation("1 w") == "1 w"
    assert validate_hilltop_interval_notation("7w") == "7w"

    assert validate_hilltop_interval_notation("010 months") == "010 months"
    assert validate_hilltop_interval_notation("10 month") == "10 month"
    assert validate_hilltop_interval_notation("10months") == "10months"
    assert validate_hilltop_interval_notation(".10month") == ".10month"
    assert validate_hilltop_interval_notation("10 mo") == "10 mo"
    assert validate_hilltop_interval_notation("10mo") == "10mo"

    assert validate_hilltop_interval_notation("10 years") == "10 years"
    assert validate_hilltop_interval_notation("10 year") == "10 year"
    assert validate_hilltop_interval_notation(".5years") == ".5years"
    assert validate_hilltop_interval_notation("10year") == "10year"
    assert validate_hilltop_interval_notation("10 y") == "10 y"
    assert validate_hilltop_interval_notation("10y") == "10y"

    # Invalid cases
    with pytest.raises(HilltopRequestError):
        validate_hilltop_interval_notation(None)
    with pytest.raises(HilltopRequestError):
        validate_hilltop_interval_notation("")
    with pytest.raises(HilltopRequestError):
        validate_hilltop_interval_notation("invalid")
    with pytest.raises(HilltopRequestError):
        validate_hilltop_interval_notation("10,000 seconds")
    with pytest.raises(HilltopRequestError):
        validate_hilltop_interval_notation("15parsecs")
    with pytest.raises(HilltopRequestError):
        validate_hilltop_interval_notation("15 parsecs")
