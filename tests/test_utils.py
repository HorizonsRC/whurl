from pathlib import Path

import pytest
import warnings
import xmltodict
from datetime import datetime, timezone, timedelta
import pandas as pd

from whurl.utils import validate_datetime, NZST, sanitise_xml_attributes
from whurl.schemas.responses.site_info import SiteInfoResponse
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

# -----------------------------------------------------------------------------
# sanitise_xml_attributes must repair bad attribute values and nothing else.
#
# Background
# ----------
# Hilltop can send attribute values containing characters that are not legal
# in XML, most often a bare ``&`` in a site name (``Name="Smith & Sons"``).
# xmltodict then refuses the whole document, so the response is cleaned first.
#
# The old implementation used the pattern ``="([^"]*.*)"``. The greedy ``.*``
# ran from the first ``="`` to the LAST quote on the line, which meant:
#
# * two attributes on one line were treated as a single value, and the quote
#   between them was rewritten to ``&quot;``, corrupting the tag;
# * a document with no line breaks was one enormous match;
# * an already-escaped ``&amp;`` was escaped again to ``&amp;amp;``;
# * it also rewrote ``="`` sequences in element text, not just in tags.
#
# The rules these tests pin down:
#
# * Only attribute values are touched, and each one separately.
# * Characters that are illegal in a value are escaped; legal entities
#   (``&amp;``, ``&#38;`` ...) are left alone, so running it twice changes
#   nothing.
# * A double quote *inside* a value is tolerated when the value is followed by
#   the end of the tag or by another attribute, because the server does not
#   escape those either.
# * A well-formed document means the same thing before and after.

MOCKED_DATA = Path(__file__).parent / "mocked_data"


def site_names(xml: str) -> list[str]:
    """Parse a cleaned document and return its site names."""
    doc = xmltodict.parse(sanitise_xml_attributes(xml))
    sites = doc["HilltopServer"]["Site"]
    if not isinstance(sites, list):
        sites = [sites]
    return [s["@Name"] for s in sites]


@pytest.mark.unit
class TestIllegalCharacters:
    def test_bare_ampersand_is_escaped(self):
        xml = '<HilltopServer><Site Name="Smith & Sons"/></HilltopServer>'

        assert site_names(xml) == ["Smith & Sons"]


    def test_angle_brackets_are_escaped(self):
        xml = '<HilltopServer><Site Name="Rain > 5 < 10"/></HilltopServer>'

        assert site_names(xml) == ["Rain > 5 < 10"]


    def test_docstring_example(self):
        assert (
            sanitise_xml_attributes('name="value with & < > characters"')
            == 'name="value with &amp; &lt; &gt; characters"'
        )

    def test_a_double_quote_inside_a_value_is_tolerated(self):
        xml = '<HilltopServer><Site Name="The "Big" Creek"/></HilltopServer>'

        assert site_names(xml) == ['The "Big" Creek']


@pytest.mark.unit
class TestEachAttributeOnItsOwn:
    def test_two_attributes_on_one_line_are_not_merged(self):
        xml = (
            '<HilltopServer><Site Name="A & B" Code="X1"/></HilltopServer>'
        )

        doc = xmltodict.parse(sanitise_xml_attributes(xml))

        site = doc["HilltopServer"]["Site"]
        assert site["@Name"] == "A & B"
        assert site["@Code"] == "X1"

    def test_a_clean_attribute_is_left_exactly_as_it_was(self):
        xml = '<Site Name="A & B" Code="X1"/>'

        assert 'Code="X1"' in sanitise_xml_attributes(xml)

    def test_a_document_on_a_single_line_still_parses(self):
        # No line breaks at all: the old pattern made this one big match.
        xml = (
            '<?xml version="1.0"?><HilltopServer><Agency>Test</Agency>'
            '<Site Name="First & Co"/><Site Name="Second"/>'
            '<Site Name="Third > Fourth"/></HilltopServer>'
        )

        assert site_names(xml) == ["First & Co", "Second", "Third > Fourth"]

    def test_the_same_document_with_line_breaks_gives_the_same_answer(self):
        one_line = (
            '<HilltopServer><Site Name="A & B" Code="1"/>'
            '<Site Name="C" Code="2"/></HilltopServer>'
        )
        spread_out = one_line.replace("><", ">\n<")
        
        assert site_names(one_line) == site_names(spread_out)


@pytest.mark.unit
class TestLegalContentIsLeftAlone:
    
    def test_existing_entities_are_not_escaped_again(self):
        xml = '<HilltopServer><Site Name="A &amp; B"/></HilltopServer>'
 
        assert sanitise_xml_attributes(xml) == xml
        assert site_names(xml) == ["A & B"]
 
    @pytest.mark.parametrize("entity", ["&#38;", "&#x26;", "&lt;", "&gt;", "&quot;"])
    def test_other_entities_survive(self, entity):
        xml = f'<Site Name="A {entity} B"/>'
 
        assert sanitise_xml_attributes(xml) == xml
 
    def test_running_it_twice_changes_nothing(self):
        xml = '<Site Name="A & B" Code="Rain > 5"/>'
 
        once = sanitise_xml_attributes(xml)
 
        assert sanitise_xml_attributes(once) == once
 
    def test_the_xml_declaration_is_untouched(self):
        xml = '<?xml version="1.0" ?><Hilltop/>'
 
        assert sanitise_xml_attributes(xml) == xml
 
    def test_equals_and_quotes_in_element_text_are_not_rewritten(self):
        xml = '<Hilltop><Comment>set a="b" later</Comment></Hilltop>'
 
        assert sanitise_xml_attributes(xml) == xml
 
    def test_an_ampersand_in_element_text_is_not_this_functions_job(self):
        # Only attribute values are repaired. Text is a separate problem.
        xml = "<Hilltop><Comment>A & B</Comment></Hilltop>"
 
        assert sanitise_xml_attributes(xml) == xml
 
 
@pytest.mark.unit
class TestRealDocuments:
    @pytest.mark.parametrize(
        "path",
        sorted(MOCKED_DATA.glob("*/*.xml")),
        ids=lambda p: f"{p.parent.name}/{p.name}",
    )
    def test_a_well_formed_document_means_the_same_after_cleaning(self, path):
        xml = path.read_text()
 
        assert xmltodict.parse(sanitise_xml_attributes(xml)) == xmltodict.parse(
            xml
        )
 
 
@pytest.mark.unit
class TestThroughSiteInfoResponse:
    def test_a_site_name_with_an_ampersand_end_to_end(self):
        xml = (
            '<?xml version="1.0"?>'
            "<HilltopServer><Agency>Test Council</Agency>"
            '<Site Name="Smith & Sons"><Altitude>5</Altitude></Site>'
            "</HilltopServer>"
        )
 
        response = SiteInfoResponse.from_xml(xml)
 
        assert response.site[0].name == "Smith & Sons"
 
    def test_two_sites_on_a_single_line_end_to_end(self):
        xml = (
            "<HilltopServer><Agency>Test Council</Agency>"
            '<Site Name="One & Two"><Altitude>5</Altitude></Site>'
            '<Site Name="Three"><Altitude>6</Altitude></Site>'
            "</HilltopServer>"
        )
 
        response = SiteInfoResponse.from_xml(xml)
 
        assert [s.name for s in response.site] == ["One & Two", "Three"]
