import os
import pytest
import pandas as pd
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
    assert data.timeseries.index.dtype == "datetime64[ns]"

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
