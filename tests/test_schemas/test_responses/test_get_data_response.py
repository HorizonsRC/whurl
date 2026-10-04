import os
import pytest
import pandas as pd
import xmltodict
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv

from whurl.client import HilltopClient
from whurl.schemas.requests import GetDataRequest
from whurl.schemas.responses import GetDataResponse
from whurl.schemas.responses.get_data import ItemInfo

load_dotenv()


# ============================================================================
# Helper Functions
# ============================================================================

def get_env(key: str) -> str:
    """Get environment variable or skip test if missing."""
    value = os.getenv(key, None)
    if value is None:
        pytest.skip(f"Missing environment variable: {key}")
    else:
        return value


def build_test_url(base_url: str, hts_endpoint: str, **kwargs) -> str:
    """Build a test URL with the given parameters."""
    return GetDataRequest(
        base_url=base_url,
        hts_endpoint=hts_endpoint,
        **kwargs,
    ).gen_url()


def assert_response_structure(
    result: GetDataResponse,
    expected_agency: str,
    expected_site: str,
    expected_measurement: str,
    expected_data_source: str | None = None,
    expected_ts_type: str = "StdSeries",
) -> GetDataResponse.Measurement:
    """Assert basic response structure and return the first measurement."""
    # Top level
    assert isinstance(result, GetDataResponse)
    assert result.agency == expected_agency
    assert isinstance(result.request, GetDataRequest)

    # Measurements
    assert len(result.measurements) > 0
    assert isinstance(result.measurements, list)

    # Find the measurement
    measurement = next(
        (m for m in result.measurements if m.site_name == expected_site),
        None,
    )
    assert measurement is not None
    assert isinstance(measurement, GetDataResponse.Measurement)

    # Data Source
    data_source = measurement.data_source
    assert isinstance(data_source, GetDataResponse.Measurement.DataSource)
    if expected_data_source:
        assert data_source.name == expected_data_source
    assert data_source.ts_type == expected_ts_type

    # Item Info
    assert len(data_source.item_info) > 0
    item_info = data_source.item_info[0]
    assert isinstance(item_info, ItemInfo)
    assert item_info.item_name == expected_measurement

    # Data
    data = measurement.data
    assert isinstance(data, GetDataResponse.Measurement.Data)
    assert data.date_format == "Calendar"
    assert isinstance(data.timeseries, pd.DataFrame)
    assert len(data.timeseries) > 0
    assert data.timeseries.index.name == "DateTime"
    assert expected_measurement in data.timeseries.columns
    assert pd.api.types.is_datetime64_any_dtype(data.timeseries.index)

    return measurement


def assert_measurement_data(
    measurement: GetDataResponse.Measurement,
    expected_item_name: str,
    expected_item_format: str = "F",
    expected_units: str = "mm",
    expected_format: str = "####",
    expected_num_items: int = 1,
    expected_interpolation: str = "Instant",
    expected_dt_item_format: str | None = None,
    expected_divisor: int | None = None,
) -> None:
    """Assert measurement data source and item info."""
    data_source = measurement.data_source
    assert data_source.num_items == expected_num_items
    assert data_source.data_type == "SimpleTimeSeries"
    assert data_source.interpolation == expected_interpolation
    assert data_source.item_format == expected_dt_item_format
    assert len(data_source.item_info) == expected_num_items

    item_info = data_source.item_info[0]
    assert item_info.item_number == 1
    assert item_info.item_name == expected_item_name
    assert item_info.item_format == expected_item_format
    assert item_info.divisor == expected_divisor
    assert item_info.units == expected_units
    assert item_info.format == expected_format

MOWSECS_2023_01_01 = 2619302400

def as_list(value) -> list:
    """xmltodict returns a bare dict for a single element; normalise to a list."""
    return value if isinstance(value, list) else [value]


def parse_output(response: GetDataResponse, **kwargs) -> dict:
    """Serialise a response with to_xml and parse it back into a plain dict."""
    return xmltodict.parse(response.to_xml(**kwargs))["Hilltop"]


def make_xml(
    data: str,
    date_format: str = "Calendar",
    item_format: str = "F",
    fmt: str = "####",
    divisor: str | None = None,
    extra_measurement: str = "",
) -> str:
    """Build a minimal single-item GetData XML document."""
    divisor_xml = f"<Divisor>{divisor}</Divisor>" if divisor is not None else ""
    return f"""<?xml version="1.0" ?>
<Hilltop>
    <Agency>Test Council</Agency>
    <Measurement SiteName="Test Site Alpha">
        <DataSource Name="Water Level" NumItems="1">
            <TSType>StdSeries</TSType>
            <DataType>SimpleTimeSeries</DataType>
            <Interpolation>Instant</Interpolation>
            <ItemInfo ItemNumber="1">
                <ItemName>Stage</ItemName>
                <ItemFormat>{item_format}</ItemFormat>
                {divisor_xml}
                <Units>mm</Units>
                <Format>{fmt}</Format>
            </ItemInfo>
        </DataSource>
        <Data DateFormat="{date_format}" NumItems="1">
            {data}
        </Data>
        {extra_measurement}
    </Measurement>
</Hilltop>
"""


def assert_round_trip(original: GetDataResponse) -> GetDataResponse:
    """Assert from_xml(to_xml(x)) preserves x, and return the re-parsed reponse."""
    xml = original.to_xml()
    reparsed = GetDataResponse.from_xml(xml)
    assert reparsed.agency == original.agency
    assert len(reparsed.measurements) == len(original.measurements)

    assert reparsed.agency == original.agency
    assert len(reparsed.measurements) == len(original.measurements)

    for before, after in zip(original.measurements, reparsed.measurements):
        assert after.site_name == before.site_name
        assert after.data_source.to_dict() == before.data_source.to_dict()
        assert after.data.date_format == before.data.date_format
        pd.testing.assert_frame_equal(
            after.data.timeseries,
            before.data.timeseries,
            # Datetime resolution (s vs us) can differ after re-parsing.
            check_dtype=False,
        )

    print(reparsed.to_xml())
    print(xml)
    # Serialising again must be stable.
    assert reparsed.to_xml() == xml
    return reparsed


def assert_output_matches_response(response: GetDataResponse) -> None:
    """Assert the to_xml output structurally agrees with the parsed response.

    Only uses values derived from the response itself, so it works for cached
    real-server data where site and measurement names are not known up front.
    """
    root = parse_output(response)
    assert root.get("Agency") == response.agency

    output_measurements = as_list(root["Measurement"])
    assert len(output_measurements) == len(response.measurements)

    for out, measurement in zip(output_measurements, response.measurements):
        assert out["@SiteName"] == measurement.site_name
        assert out["DataSource"]["@Name"] == measurement.data_source.name

        expected_numbers = [
            str(i.item_number) for i in measurement.data_source.item_info
        ]
        out_items = as_list(out["DataSource"]["ItemInfo"])
        assert [i["@ItemNumber"] for i in out_items] == expected_numbers

        rows = as_list(out["Data"].get("E", []))
        assert len(rows) == len(measurement.data.timeseries)
        for row in rows:
            assert {f"I{n}" for n in expected_numbers} <= set(row)


# ============================================================================
# Fixture Factory
# ============================================================================

def create_cached_fixture(filename: str, request_kwargs: dict | None = None):
    """Factory to create cached XML fixtures."""

    @pytest.fixture
    def fixture_func(request, httpx_mock, remote_client):
        path = (
            Path(__file__).parent.parent.parent
            / "fixture_cache"
            / "get_data"
            / filename
        )

        if request.config.getoption("--update"):
            httpx_mock._options.should_mock = (
                lambda req: req.url.host != urlparse(remote_client.base_url).netloc
            )
            cached_url = build_test_url(
                base_url=remote_client.base_url,
                hts_endpoint=remote_client.hts_endpoint,
                **(request_kwargs or {}),
            )
            cached_xml = remote_client.session.get(cached_url).text
            path.write_text(cached_xml, encoding="utf-8")

        if not path.exists():
            pytest.skip(
                f"Fixture cache file not found: {path.name}. "
                "Use --update flag to populate from remote API."
            )

        return path.read_text(encoding="utf-8")

    return fixture_func


def create_mocked_fixture(filename: str):
    """Factory to create mocked XML fixtures."""

    @pytest.fixture
    def fixture_func():
        path = (
            Path(__file__).parent.parent.parent
            / "mocked_data"
            / "get_data"
            / filename
        )
        return path.read_text(encoding="utf-8")

    return fixture_func


# ============================================================================
# Fixtures
# ============================================================================

# Cached fixtures
basic_response_xml_cached = create_cached_fixture(
    "basic_response.xml",
    {
        "site": os.getenv("TEST_SITE"),
        "measurement": os.getenv("TEST_MEASUREMENT"),
        "from_datetime": "2025-01-01T00:00:00",
        "to_datetime": "2025-02-01T00:00:00",
    },
)

one_point_response_xml_cached = create_cached_fixture(
    "one_point_response.xml",
    {
        "site": os.getenv("TEST_SITE"),
        "measurement": os.getenv("TEST_MEASUREMENT"),
    },
)

quality_response_xml_cached = create_cached_fixture(
    "quality_response.xml",
    {
        "site": os.getenv("TEST_SITE"),
        "measurement": os.getenv("TEST_MEASUREMENT"),
        "from_datetime": "2023-01-01T00:00:00",
        "to_datetime": "2025-01-01T00:00:00",
        "ts_type": "StdQualSeries",
    },
)

check_response_xml_cached = create_cached_fixture(
    "check_response.xml",
    {
        "site": os.getenv("TEST_SITE"),
        "measurement": os.getenv("TEST_MEASUREMENT"),
        "from_datetime": "2025-01-01T00:00:00",
        "to_datetime": "2026-01-01T00:00:00",
        "ts_type": "CheckSeries",
    },
)

collection_response_xml_cached = create_cached_fixture(
    "collection_response.xml",
    {
        "site": os.getenv("TEST_SITE"),
        "measurement": os.getenv("TEST_MEASUREMENT"),
        "collection": os.getenv("TEST_COLLECTION"),
        "from_datetime": "2025-01-01T00:00:00",
        "to_datetime": "2025-02-01T00:00:00",
    },
)

time_interval_response_xml_cached = create_cached_fixture(
    "time_interval_response.xml",
    {
        "site": os.getenv("TEST_SITE"),
        "measurement": os.getenv("TEST_MEASUREMENT"),
        "time_interval": "2025-01-01T12:00:00/2025-01-02T12:00:00",
    },
)

time_interval_complex_response_xml_cached = create_cached_fixture(
    "time_interval_response.xml",
    {
        "site": os.getenv("TEST_SITE"),
        "measurement": os.getenv("TEST_MEASUREMENT"),
        "time_interval": "2025-01-01T12:00:00/P2DT2H",
        "alignment": "3h",
    },
)

date_only_response_xml_cached = create_cached_fixture(
    "date_only_response.xml",
    {
        "site": os.getenv("TEST_SITE"),
        "measurement": os.getenv("TEST_MEASUREMENT"),
        "time_interval": "2025-01-01T12:00:00/P2DT2H",
        "date_only": "Yes",
    },
)

# Mocked fixtures
basic_response_xml_mocked = create_mocked_fixture("basic_response.xml")
one_point_response_xml_mocked = create_mocked_fixture("one_point_response.xml")
quality_response_xml_mocked = create_mocked_fixture("quality_response.xml")
check_response_xml_mocked = create_mocked_fixture("check_response.xml")
collection_response_xml_mocked = create_mocked_fixture("collection_response.xml")
time_interval_response_xml_mocked = create_mocked_fixture(
    "time_interval_response.xml"
)
time_interval_complex_response_xml_mocked = create_mocked_fixture(
    "time_interval_complex_response.xml"
)
date_only_response_xml_mocked = create_mocked_fixture("date_only_response.xml")


# ============================================================================
# Test Classes
# ============================================================================

class TestRemoteFixtures:
    """Test that cached fixtures match remote API responses."""

    @pytest.mark.remote
    @pytest.mark.integration
    def test_basic_response(self, remote_client, httpx_mock, basic_response_xml_cached):
        """Test basic_response_xml_cached matches remote."""
        self._assert_remote_matches_cached(
            remote_client=remote_client,
            httpx_mock=httpx_mock,
            cached_xml=basic_response_xml_cached,
            site=get_env("TEST_SITE"),
            measurement=get_env("TEST_MEASUREMENT"),
            from_datetime="2025-01-01T00:00:00",
            to_datetime="2025-02-01T00:00:00",
        )

    @pytest.mark.remote
    @pytest.mark.integration
    def test_one_point_response(self, remote_client, httpx_mock, one_point_response_xml_cached):
        """Test one_point_response_xml_cached matches remote."""
        self._assert_remote_matches_cached(
            remote_client=remote_client,
            httpx_mock=httpx_mock,
            cached_xml=one_point_response_xml_cached,
            site=get_env("TEST_SITE"),
            measurement=get_env("TEST_MEASUREMENT"),
        )

    @pytest.mark.remote
    @pytest.mark.integration
    def test_check_response(self, remote_client, httpx_mock, check_response_xml_cached):
        """Test check_response_xml_cached matches remote."""
        self._assert_remote_matches_cached(
            remote_client=remote_client,
            httpx_mock=httpx_mock,
            cached_xml=check_response_xml_cached,
            site=get_env("TEST_SITE"),
            measurement=get_env("TEST_MEASUREMENT"),
            from_datetime="2025-01-01T00:00:00",
            to_datetime="2026-01-01T00:00:00",
            ts_type="CheckSeries",
        )
        
    @pytest.mark.remote
    @pytest.mark.integration
    def test_quality_response(self, remote_client, httpx_mock, quality_response_xml_cached):
        """Test quality_response_xml_cached matches remote."""
        self._assert_remote_matches_cached(
            remote_client=remote_client,
            httpx_mock=httpx_mock,
            cached_xml=quality_response_xml_cached,
            site=get_env("TEST_SITE"),
            measurement=get_env("TEST_MEASUREMENT"),
            from_datetime="2023-01-01T00:00:00",
            to_datetime="2025-01-01T00:00:00",
            ts_type="StdQualSeries",
        )

    @pytest.mark.remote
    @pytest.mark.integration
    def test_collection_response(self, remote_client, httpx_mock, collection_response_xml_cached):
        """Test collection_response_xml_cached matches remote."""
        self._assert_remote_matches_cached(
            remote_client=remote_client,
            httpx_mock=httpx_mock,
            cached_xml=collection_response_xml_cached,
            collection=get_env("TEST_COLLECTION"),
            from_datetime="2025-01-01T00:00:00",
            to_datetime="2025-02-01T00:00:00",
        )

    @pytest.mark.remote
    @pytest.mark.integration
    def test_time_interval_response(self, remote_client, httpx_mock, time_interval_response_xml_cached):
        """Test time_interval_response_xml_cached matches remote."""
        self._assert_remote_matches_cached(
            remote_client=remote_client,
            httpx_mock=httpx_mock,
            cached_xml=time_interval_response_xml_cached,
            site=get_env("TEST_SITE"),
            measurement=get_env("TEST_MEASUREMENT"),
            time_interval="2025-01-01T12:00:00/2025-01-02T12:00:00",
        )

    @pytest.mark.remote
    @pytest.mark.integration
    def test_time_interval_complex_response(self, remote_client, httpx_mock, time_interval_complex_response_xml_cached):
        """Test time_interval_complex_response_xml_cached matches remote."""
        self._assert_remote_matches_cached(
            remote_client=remote_client,
            httpx_mock=httpx_mock,
            cached_xml=time_interval_complex_response_xml_cached,
            site=get_env("TEST_SITE"),
            measurement=get_env("TEST_MEASUREMENT"),
            time_interval="2025-01-01T12:00:00/P2DT2H",
            alignment="3h",
        )

    @pytest.mark.remote
    @pytest.mark.integration
    def test_date_only_response(self, remote_client, httpx_mock, date_only_response_xml_cached):
        """Test date_only_response_xml_cached matches remote."""
        remote_url = build_test_url(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            site=get_env("TEST_SITE"),
            measurement=get_env("TEST_MEASUREMENT"),
            time_interval="2025-01-01T12:00:00/P2DT2H",
            date_only="Yes",
        )

        httpx_mock._options.should_mock = (
            lambda req: req.url.host != urlparse(remote_client.base_url).netloc
        )

        remote_xml = remote_client.session.get(remote_url).text
        assert date_only_response_xml_cached == remote_xml

    # ========================================================================
    # Helper method for remote fixture tests
    # ========================================================================

    def _assert_remote_matches_cached(
        self,
        remote_client,
        httpx_mock,
        cached_xml: str,
        **request_kwargs,
    ) -> None:
        """Assert that a cached XML matches the remote response."""
        from tests.conftest import remove_tags

        remote_url = build_test_url(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            **request_kwargs,
        )

        httpx_mock._options.should_mock = (
            lambda req: req.url.host != urlparse(remote_client.base_url).netloc
        )

        remote_xml = remote_client.session.get(remote_url).text

        # Remove time tags (will change often)
        remote_cleaned = remove_tags(remote_xml, ["T", "E"])
        cached_cleaned = remove_tags(cached_xml, ["T", "E"])

        assert cached_cleaned == remote_cleaned


class TestResponseValidation:
    """Test response validation with mocked and cached data."""

    # ========================================================================
    # Basic Response Tests
    # ========================================================================

    @pytest.mark.unit
    def test_basic_response_unit(self, httpx_mock, basic_response_xml_mocked):
        """Test basic XML response with mocked data."""
        result = self._make_request_and_parse(
            httpx_mock=httpx_mock,
            xml=basic_response_xml_mocked,
            site="Test Site Alpha",
            measurement="Stage",
            from_datetime="2025-01-01T00:00:00",
            to_datetime="2025-02-01T00:00:00",
        )

        measurement = assert_response_structure(
            result=result,
            expected_agency="Test Council",
            expected_site="Test Site Alpha",
            expected_measurement="Stage",
            expected_data_source="Water Level",
        )

        assert_measurement_data(
            measurement=measurement,
            expected_item_name="Stage",
        )

        # Check dataframe conversion
        df = result.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    @pytest.mark.integration
    def test_basic_response_integration(self, httpx_mock, basic_response_xml_cached):
        """Test basic XML response with cached data."""
        result = self._make_request_and_parse(
            httpx_mock=httpx_mock,
            xml=basic_response_xml_cached,
            site=get_env("TEST_SITE"),
            measurement=get_env("TEST_MEASUREMENT"),
            from_datetime="2025-01-01T00:00:00",
            to_datetime="2025-01-02T00:00:00",
        )

        assert_response_structure(
            result=result,
            expected_agency=get_env("TEST_AGENCY"),
            expected_site=get_env("TEST_SITE"),
            expected_measurement=get_env("TEST_MEASUREMENT"),
            expected_data_source=get_env("TEST_DATA_SOURCE"),
        )


    # ========================================================================
    # Check Response Tests
    # ========================================================================
    
    @pytest.mark.unit
    def test_check_response_unit(self, httpx_mock, check_response_xml_mocked):
        """Test check XML response with mocked data."""
        result = self._make_request_and_parse(
            httpx_mock=httpx_mock,
            xml=check_response_xml_mocked,
            site="Test Site Alpha",
            measurement="Stage",
            from_datetime="2025-01-01T00:00:00",
            to_datetime="2026-01-01T00:00:00",
            ts_type="CheckSeries",
        )

        measurement = assert_response_structure(
            result=result,
            expected_agency="Test Council",
            expected_site="Test Site Alpha",
            expected_measurement="Check Level",
            expected_data_source="Water Level",
            expected_ts_type="CheckSeries",
        )

        assert_measurement_data(
            measurement=measurement,
            expected_item_name="Check Level",
            expected_num_items=3,
            expected_interpolation="Discrete",
            expected_dt_item_format="45",
            expected_units="hPa",
            expected_divisor=1,
            expected_format="####.#"
        )

        # Check dataframe conversion
        df = result.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        
        # Check df type conversion
        for i, row in df.iterrows():
            assert isinstance(row["Check Level"], float)
            assert isinstance(row["Recorder Time"], pd.Timestamp)
            assert isinstance(row["Comment"], (str, type(pd.NA)))
        
    @pytest.mark.integration
    def test_check_response_integration(self, httpx_mock, check_response_xml_cached):
        """Test check XML response with cached data."""
        result = self._make_request_and_parse(
            httpx_mock=httpx_mock,
            xml=check_response_xml_cached,
            site=get_env("TEST_SITE"),
            measurement=get_env("TEST_MEASUREMENT"),
            from_datetime="2025-01-01T00:00:00",
            to_datetime="2026-01-01T00:00:00",
            ts_type="CheckSeries",
        )

        assert_response_structure(
            result=result,
            expected_agency=get_env("TEST_AGENCY"),
            expected_site=get_env("TEST_SITE"),
            expected_measurement=get_env("TEST_CHECK_MEASUREMENT"),
            expected_data_source=get_env("TEST_DATA_SOURCE"),
            expected_ts_type="CheckSeries"
        )
        
        # Check dataframe conversion
        df = result.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        
        # Check df type conversion
        for i, row in df.iterrows():
            print(row)
            assert isinstance(row[get_env("TEST_CHECK_MEASUREMENT")], float)
            assert isinstance(row["Recorder Time"], pd.Timestamp)
            assert isinstance(row["Comment"], (str, type(pd.NA)))

    # ========================================================================
    # Quality Response Tests
    # ========================================================================
    
    @pytest.mark.unit
    def test_quality_response_unit(self, httpx_mock, quality_response_xml_mocked):
        """Test quality XML response with mocked data."""
        result = self._make_request_and_parse(
            httpx_mock=httpx_mock,
            xml=quality_response_xml_mocked,
            site="Test Site Alpha",
            measurement="Stage",
            from_datetime="2025-01-01T00:00:00",
            to_datetime="2026-01-01T00:00:00",
            ts_type="StdQualSeries",
        )

        measurement = assert_response_structure(
            result=result,
            expected_agency="Test Council",
            expected_site="Test Site Alpha",
            expected_measurement="Atmospheric Pressure",
            expected_data_source="Atmospheric Pressure",
            expected_ts_type="StdQualSeries",
        )

        assert_measurement_data(
            measurement=measurement,
            expected_item_name="Atmospheric Pressure",
            expected_num_items=1,
            expected_interpolation="Event",
            expected_dt_item_format=None,
            expected_units="hPa",
            expected_format="#.#"
        )

        # Check dataframe conversion
        df = result.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        
        # Check df type conversion
        for i, row in df.iterrows():
            assert isinstance(row["Atmospheric Pressure"], float)
        
    @pytest.mark.integration
    def test_quality_response_integration(self, httpx_mock, quality_response_xml_cached):
        """Test quality XML response with cached data."""
        result = self._make_request_and_parse(
            httpx_mock=httpx_mock,
            xml=quality_response_xml_cached,
            site=get_env("TEST_SITE"),
            measurement=get_env("TEST_MEASUREMENT"),
            from_datetime="2024-01-01T00:00:00",
            to_datetime="2025-01-01T00:00:00",
            ts_type="StdQualSeries",
        )

        assert_response_structure(
            result=result,
            expected_agency=get_env("TEST_AGENCY"),
            expected_site=get_env("TEST_SITE"),
            expected_measurement=get_env("TEST_MEASUREMENT"),
            expected_data_source=get_env("TEST_DATA_SOURCE"),
            expected_ts_type="StdQualSeries"
        )
        
        # Check dataframe conversion
        df = result.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        
        # Check df type conversion
        for i, row in df.iterrows():
            print(row)
            assert isinstance(row[get_env("TEST_MEASUREMENT")], float)

    # ========================================================================
    # Collection Response Tests
    # ========================================================================

    @pytest.mark.unit
    def test_collection_response_unit(self, httpx_mock, collection_response_xml_mocked):
        """Test collection response with mocked data."""
        start_time = pd.Timestamp.now() - pd.Timedelta(hours=48)
        start_timestamp = start_time.strftime("%Y-%m-%dT%H:%M:%S")

        result = self._make_request_and_parse(
            httpx_mock=httpx_mock,
            xml=collection_response_xml_mocked,
            collection="Rainfall",
            from_datetime=start_timestamp,
        )

        measurement = assert_response_structure(
            result=result,
            expected_agency="Test Council",
            expected_site="Test Site Alpha",
            expected_measurement="Stage",
            expected_data_source="Water Level",
        )

        assert_measurement_data(
            measurement=measurement,
            expected_item_name="Stage",
        )

    @pytest.mark.integration
    def test_collection_response_integration(self, httpx_mock, collection_response_xml_cached):
        """Test collection response with cached data."""
        result = self._make_request_and_parse(
            httpx_mock=httpx_mock,
            xml=collection_response_xml_cached,
            collection=get_env("TEST_COLLECTION"),
            from_datetime="2025-01-01T00:00:00",
            to_datetime="2025-02-01T00:00:00",
        )

        assert_response_structure(
            result=result,
            expected_agency=get_env("TEST_AGENCY"),
            expected_site=get_env("TEST_SITE"),
            expected_measurement=get_env("TEST_MEASUREMENT"),
            expected_data_source=get_env("TEST_DATA_SOURCE"),
        )

    # ========================================================================
    # One Point Response Tests
    # ========================================================================

    @pytest.mark.unit
    def test_one_point_response_unit(self, httpx_mock, one_point_response_xml_mocked):
        """Test single point response with mocked data."""
        result = self._make_request_and_parse(
            httpx_mock=httpx_mock,
            xml=one_point_response_xml_mocked,
            site="Test Site Alpha",
            measurement="Stage",
        )

        measurement = assert_response_structure(
            result=result,
            expected_agency="Test Council",
            expected_site="Test Site Alpha",
            expected_measurement="Stage",
            expected_data_source="Water Level",
        )

        assert_measurement_data(
            measurement=measurement,
            expected_item_name="Stage",
            expected_format="#.#"
        )

        # One point response should have exactly one row
        assert len(measurement.data.timeseries) == 1

    @pytest.mark.integration
    def test_one_point_response_integration(self, httpx_mock, one_point_response_xml_cached):
        """Test single point response with cached data."""
        result = self._make_request_and_parse(
            httpx_mock=httpx_mock,
            xml=one_point_response_xml_cached,
            site=get_env("TEST_SITE"),
            measurement=get_env("TEST_MEASUREMENT"),
        )

        assert_response_structure(
            result=result,
            expected_agency=get_env("TEST_AGENCY"),
            expected_site=get_env("TEST_SITE"),
            expected_measurement=get_env("TEST_MEASUREMENT"),
            expected_data_source=get_env("TEST_DATA_SOURCE"),
        )

    # ========================================================================
    # Time Interval Response Tests
    # ========================================================================

    @pytest.mark.unit
    def test_time_interval_response_unit(self, httpx_mock, time_interval_response_xml_mocked):
        """Test time interval response with mocked data."""
        time_interval = "2025-01-01T12:00:00/2025-01-02T12:00:00"

        result = self._make_request_and_parse(
            httpx_mock=httpx_mock,
            xml=time_interval_response_xml_mocked,
            site="Test Site Alpha",
            measurement="Stage",
            time_interval=time_interval,
        )

        measurement = assert_response_structure(
            result=result,
            expected_agency="Test Council",
            expected_site="Test Site Alpha",
            expected_measurement="Stage",
            expected_data_source="Water Level",
        )

        assert_measurement_data(
            measurement=measurement,
            expected_item_name="Stage",
        )

    @pytest.mark.integration
    def test_time_interval_response_integration(self, httpx_mock, time_interval_response_xml_cached):
        """Test time interval response with cached data."""
        time_interval = "2025-01-01T12:00:00/2025-01-02T12:00:00"

        result = self._make_request_and_parse(
            httpx_mock=httpx_mock,
            xml=time_interval_response_xml_cached,
            site=get_env("TEST_SITE"),
            measurement=get_env("TEST_MEASUREMENT"),
            time_interval=time_interval,
        )

        assert_response_structure(
            result=result,
            expected_agency=get_env("TEST_AGENCY"),
            expected_site=get_env("TEST_SITE"),
            expected_measurement=get_env("TEST_MEASUREMENT"),
            expected_data_source=get_env("TEST_DATA_SOURCE"),
        )

    # ========================================================================
    # Time Interval Complex Response Tests
    # ========================================================================

    @pytest.mark.unit
    def test_time_interval_complex_response_unit(
        self, httpx_mock, time_interval_complex_response_xml_mocked
    ):
        """Test time interval response with alignment."""
        time_interval = "2025-01-01T12:00:00/P2DT2H"
        alignment = "3h"

        result = self._make_request_and_parse(
            httpx_mock=httpx_mock,
            xml=time_interval_complex_response_xml_mocked,
            site="Test Site Alpha",
            measurement="Stage",
            time_interval=time_interval,
            alignment=alignment,
        )

        measurement = assert_response_structure(
            result=result,
            expected_agency="Test Council",
            expected_site="Test Site Alpha",
            expected_measurement="Stage",
            expected_data_source="Water Level",
        )

        assert_measurement_data(
            measurement=measurement,
            expected_item_name="Stage",
        )

        # Check alignment
        data = measurement.data
        expected_start = pd.Timestamp("2025-01-01T12:00:00")
        expected_end = expected_start + pd.Timedelta(days=2, hours=2)

        assert data.timeseries.index[0] == expected_start
        assert data.timeseries.index[-1] == expected_end

    @pytest.mark.integration
    def test_time_interval_complex_response_integration(
        self, httpx_mock, time_interval_complex_response_xml_cached
    ):
        """Test time interval response with alignment."""
        time_interval = "2025-01-01T12:00:00/P2DT2H"
        alignment = "3h"

        result = self._make_request_and_parse(
            httpx_mock=httpx_mock,
            xml=time_interval_complex_response_xml_cached,
            site=get_env("TEST_SITE"),
            measurement=get_env("TEST_MEASUREMENT"),
            time_interval=time_interval,
            alignment=alignment,
        )

        measurement = assert_response_structure(
            result=result,
            expected_agency=get_env("TEST_AGENCY"),
            expected_site=get_env("TEST_SITE"),
            expected_measurement=get_env("TEST_MEASUREMENT"),
            expected_data_source=get_env("TEST_DATA_SOURCE"),
        )

        # Check alignment
        data = measurement.data
        expected_start = pd.Timestamp("2025-01-01T12:00:00")
        expected_end = expected_start + pd.Timedelta(days=2, hours=2)

        assert data.timeseries.index[0] == expected_start
        assert data.timeseries.index[-1] == expected_end

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _make_request_and_parse(
        self,
        httpx_mock,
        xml: str,
        base_url: str = "http://example.com",
        hts_endpoint: str = "foo.hts",
        **request_kwargs,
    ) -> GetDataResponse:
        """Make a request and parse the response."""
        test_url = build_test_url(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            **request_kwargs,
        )
        print(test_url)

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=xml,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            return client.get_data(**request_kwargs)


ALL_RESPONSE_NAMES = [
    "basic_response",
    "one_point_response",
    "quality_response",
    "check_response",
    "collection_response",
    "time_interval_response",
    "time_interval_complex_response",
    "date_only_response",
]


class TestToXml:
    """Test GetDataResponse.to_xml, the inverse of from_xml."""

    # ========================================================================
    # Round trip: mocked (unit) and cached (integration)
    # ========================================================================
    
    @pytest.mark.unit
    @pytest.mark.parametrize("name", ALL_RESPONSE_NAMES)
    def test_round_trip_unit(self, request, name):
        """from_xml -> to_xml -> from_xml preserves mocked responses."""
        xml = request.getfixturevalue(f"{name}_xml_mocked")
        assert_round_trip(GetDataResponse.from_xml(xml))

    @pytest.mark.integration
    @pytest.mark.parametrize("name", ALL_RESPONSE_NAMES)
    def test_round_trip_integration(self, request, name):
        """from_xml -> to_xml -> from_xml preserves cached server responses."""
        xml = request.getfixturevalue(f"{name}_xml_cached")
        assert_round_trip(GetDataResponse.from_xml(xml))

    @pytest.mark.unit
    @pytest.mark.parametrize("name", ALL_RESPONSE_NAMES)
    def assert_output_matches_response_unit(self, request, name):
        """to_xml output agrees with the parsed mocked response."""
        xml = request.getfixturevalue(f"{name}_xml_mocked")
        assert_output_matches_response(GetDataResponse.from_xml(xml))

    @pytest.mark.integration
    @pytest.mark.parametrize("name", ALL_RESPONSE_NAMES)
    def test_output_matches_response_integration(self, request, name):
        """to_xml output agrees with the parsed cached response."""
        xml = request.getfixturevalue(f"{name}_xml_cached")
        assert_output_matches_response(GetDataResponse.from_xml(xml))

    
    # ========================================================================
    # Structure
    # ========================================================================

    @pytest.mark.unit
    def test_basic_structure_unit(self, basic_response_xml_mocked):
        """Test the generated XML for the basic response in detail."""
        root = parse_output(GetDataResponse.from_xml(basic_response_xml_mocked))

        assert root["Agency"] == "Test Council"

        measurement = root["Measurement"]
        assert measurement["@SiteName"] == "Test Site Alpha"
        
        source = measurement["DataSource"]
        assert source["@Name"] == "Water Level"
        assert source["@NumItems"] == "1"
        assert source["TSType"] == "StdSeries"
        assert source["DataType"] == "SimpleTimeSeries"
        assert source["Interpolation"] == "Instant"
        assert source["ItemInfo"]["@ItemNumber"] == "1"
        assert source["ItemInfo"]["ItemName"] == "Stage"
        assert source["ItemInfo"]["ItemFormat"] == "F"
        assert source["ItemInfo"]["Units"] == "mm"
        assert source["ItemInfo"]["Format"] == "####"
 
        data = measurement["Data"]
        assert data["@DateFormat"] == "Calendar"
        assert data["@NumItems"] == "1"
        rows = as_list(data["E"])
        assert len(rows) == 13
        assert rows[0] == {"T": "2023-01-01T00:00:00", "I1": "584"}
        assert rows[-1] == {"T": "2023-01-01T01:00:00", "I1": "582"}
 
    @pytest.mark.unit
    def test_returns_xml_document_string_unit(self, basic_response_xml_mocked):
        xml = GetDataResponse.from_xml(basic_response_xml_mocked).to_xml()
 
        assert isinstance(xml, str)
        assert xml.startswith("<?xml")
        assert "<Hilltop>" in xml
 
    @pytest.mark.unit
    def test_one_point_unit(self, one_point_response_xml_mocked):
        response = GetDataResponse.from_xml(one_point_response_xml_mocked)
        rows = as_list(parse_output(response)["Measurement"]["Data"]["E"])
 
        assert rows == [{"T": "2025-09-16T08:15:00", "I1": "1021.53"}]
 
    @pytest.mark.unit
    def test_multiple_measurements_unit(self, collection_response_xml_mocked):
        response = GetDataResponse.from_xml(collection_response_xml_mocked)
        measurements = as_list(parse_output(response)["Measurement"])
 
        assert [m["DataSource"]["@Name"] for m in measurements] == [
            "Water Level",
            "Rainfall",
        ]
 
    @pytest.mark.unit
    def test_pretty_flag_unit(self, basic_response_xml_mocked):
        response = GetDataResponse.from_xml(basic_response_xml_mocked)
 
        assert "\n" in response.to_xml()
        # xmltodict still puts a newline after the XML declaration.
        body = response.to_xml(pretty=False).split("?>", 1)[1].strip()
        assert "\n" not in body
 
    @pytest.mark.unit
    def test_special_characters_are_escaped_unit(self, basic_response_xml_mocked):
        xml = basic_response_xml_mocked.replace(
            "Test Council", "Test &amp; Council &lt;NZ&gt;"
        )
        output = GetDataResponse.from_xml(xml).to_xml()
 
        assert "&amp;" in output
        assert GetDataResponse.from_xml(output).agency == "Test & Council <NZ>"
 
    @pytest.mark.unit
    def test_tideda_site_number_is_preserved_unit(self):
        xml = make_xml(
            data="<E><T>2023-01-01T00:00:00</T><I1>584</I1></E>",
        ).replace(
            "</Measurement>",
            "<TidedaSiteNumber>12345</TidedaSiteNumber></Measurement>",
        )
        response = GetDataResponse.from_xml(xml)
 
        assert parse_output(response)["Measurement"]["TidedaSiteNumber"] == "12345"
 
    @pytest.mark.unit
    def test_tideda_site_number_omitted_when_absent_unit(
        self, basic_response_xml_mocked
    ):
        response = GetDataResponse.from_xml(basic_response_xml_mocked)
 
        assert "TidedaSiteNumber" not in parse_output(response)["Measurement"]
 
    # ========================================================================
    # Value formatting
    # ========================================================================
 
    @pytest.mark.unit
    def test_float_uses_format_spec_for_decimal_places_unit(self):
        xml = make_xml(
            data="<E><T>2023-01-01T00:00:00</T><I1>12.5</I1></E>",
            fmt="####.##",
        )
        rows = as_list(
            parse_output(GetDataResponse.from_xml(xml))["Measurement"]["Data"]["E"]
        )
 
        assert rows[0]["I1"] == "12.50"
 
    @pytest.mark.unit
    def test_float_without_decimals_in_format_unit(self):
        xml = make_xml(data="<E><T>2023-01-01T00:00:00</T><I1>584</I1></E>")
        rows = as_list(
            parse_output(GetDataResponse.from_xml(xml))["Measurement"]["Data"]["E"]
        )
 
        assert rows[0]["I1"] == "584"
 
    @pytest.mark.unit
    def test_divisor_is_reapplied_unit(self):
        # Parsing divides by the divisor, so serialising must multiply it back.
        xml = make_xml(
            data="<E><T>2023-01-01T00:00:00</T><I1>5840</I1></E>",
            divisor="10",
        )
        response = GetDataResponse.from_xml(xml)
 
        assert response.measurements[0].data.timeseries["Stage"].iloc[0] == 584.0
        rows = as_list(parse_output(response)["Measurement"]["Data"]["E"])
        assert rows[0]["I1"] == "5840"
 
    @pytest.mark.unit
    def test_format_spec_decimals_are_a_floor_not_a_ceiling_unit(self):
        """The Format spec can understate a value's real precision.
 
        A real Hilltop server returned "1024.53" for an item whose Format
        is "#.#" (nominally one decimal place) - see the one_point_response
        cached fixture. to_xml must not truncate that extra precision away.
        """
        xml = make_xml(
            data="<E><T>2023-01-01T00:00:00</T><I1>1024.53</I1></E>",
            fmt="#.#",
        )
        rows = as_list(
            parse_output(GetDataResponse.from_xml(xml))["Measurement"]["Data"]["E"]
        )
 
        assert rows[0]["I1"] == "1024.53"
 
    @pytest.mark.unit
    def test_integer_item_format_unit(self):
        xml = make_xml(
            data="<E><T>2023-01-01T00:00:00</T><I1>42</I1></E>",
            item_format="I",
        )
        rows = as_list(
            parse_output(GetDataResponse.from_xml(xml))["Measurement"]["Data"]["E"]
        )
 
        assert rows[0]["I1"] == "42"
 
    @pytest.mark.unit
    def test_string_item_format_unit(self):
        xml = make_xml(
            data="<E><T>2023-01-01T00:00:00</T><I1>Some comment</I1></E>",
            item_format="S",
            fmt="###",
        )
        rows = as_list(
            parse_output(GetDataResponse.from_xml(xml))["Measurement"]["Data"]["E"]
        )
 
        assert rows[0]["I1"] == "Some comment"
 
    @pytest.mark.unit
    def test_check_response_mixed_item_formats_unit(self, check_response_xml_mocked):
        response = GetDataResponse.from_xml(check_response_xml_mocked)
        rows = as_list(parse_output(response)["Measurement"]["Data"]["E"])
 
        assert len(rows) == 2
        # F: float formatted to one decimal place (Format is "####.#").
        assert rows[0]["I1"] == "999.0"
        # D: written back as a mowsecs integer (matching the original).
        assert rows[0]["I2"] == "2696416200"
        # S: text passes through.
        assert rows[0]["I3"] == "Other. NA"
 
    @pytest.mark.unit
    def test_missing_string_value_unit(self, check_response_xml_mocked):
        response = GetDataResponse.from_xml(check_response_xml_mocked)
        rows = as_list(parse_output(response)["Measurement"]["Data"]["E"])
 
        # xmltodict reads an empty element as None.
        assert rows[1]["I3"] is None
        reparsed = GetDataResponse.from_xml(response.to_xml())
        assert pd.isna(reparsed.measurements[0].data.timeseries["Comment"].iloc[1])
 
    @pytest.mark.unit
    def test_item_info_order_is_preserved_unit(self, check_response_xml_mocked):
        response = GetDataResponse.from_xml(check_response_xml_mocked)
        items = parse_output(response)["Measurement"]["DataSource"]["ItemInfo"]
 
        assert [i["@ItemNumber"] for i in items] == ["1", "3", "2"]
 
    @pytest.mark.unit
    def test_data_source_item_format_is_preserved_unit(
        self, check_response_xml_mocked
    ):
        response = GetDataResponse.from_xml(check_response_xml_mocked)
 
        assert parse_output(response)["Measurement"]["DataSource"]["ItemFormat"] == "45"
 
    # ========================================================================
    # Date formats
    # ========================================================================
 
    @pytest.mark.unit
    def test_calendar_dates_unit(self, basic_response_xml_mocked):
        response = GetDataResponse.from_xml(basic_response_xml_mocked)
        rows = as_list(parse_output(response)["Measurement"]["Data"]["E"])
 
        assert all("T" in row and "D" not in row for row in rows)
        assert rows[1]["T"] == "2023-01-01T00:05:00"
 
    @pytest.mark.unit
    def test_mowsecs_dates_unit(self):
        xml = make_xml(
            data=f"<E><T>{MOWSECS_2023_01_01}</T><I1>584</I1></E>",
            date_format="mowsecs",
        )
        response = GetDataResponse.from_xml(xml)
 
        timeseries = response.measurements[0].data.timeseries
        assert timeseries.index[0] == pd.Timestamp("2023-01-01T00:00:00")
 
        data = parse_output(response)["Measurement"]["Data"]
        assert data["@DateFormat"] == "mowsecs"
        assert data["E"]["T"] == str(MOWSECS_2023_01_01)
 
    @pytest.mark.unit
    def test_date_only_uses_d_tag_unit(self, date_only_response_xml_mocked):
        response = GetDataResponse.from_xml(date_only_response_xml_mocked)
        rows = as_list(parse_output(response)["Measurement"]["Data"]["E"])
 
        assert len(rows) == 29
        assert all("D" in row and "T" not in row for row in rows)
        assert rows[0] == {"D": "2023-01-01", "I1": "573"}
 
    @pytest.mark.integration
    def test_date_only_uses_d_tag_integration(self, date_only_response_xml_cached):
        response = GetDataResponse.from_xml(date_only_response_xml_cached)
        rows = as_list(parse_output(response)["Measurement"]["Data"]["E"])
 
        assert len(rows) > 0
        assert all("D" in row and "T" not in row for row in rows)
 
    # ========================================================================
    # Edge cases
    # ========================================================================
 
    @pytest.mark.unit
    def test_no_measurements_unit(self):
        response = GetDataResponse(Agency="Test Council")
 
        assert parse_output(response) == {"Agency": "Test Council"}
        reparsed = GetDataResponse.from_xml(response.to_xml())
        assert reparsed.agency == "Test Council"
        assert reparsed.measurements == []
