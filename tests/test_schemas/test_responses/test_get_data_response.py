import os

import pandas as pd
import pytest
from dotenv import load_dotenv

load_dotenv()


def create_cached_fixtures(filename: str, request_kwargs: dict = None):
    """Factory to create cached fixtures."""

    @pytest.fixture
    def fixture_func(request, httpx_mock, remote_client):
        """Load test XML once per test session."""
        from pathlib import Path
        from urllib.parse import urlparse

        from hurl.schemas.requests import GetDataRequest

        path = (
            Path(__file__).parent.parent.parent
            / "fixture_cache"
            / "get_data"
            / filename
        )
        if request.config.getoption("--update"):
            # Switch off httpx mock so that cached request can go through.
            httpx_mock._options.should_mock = (
                lambda request: request.url.host
                != urlparse(remote_client.base_url).netloc
            )
            cached_url = GetDataRequest(
                base_url=remote_client.base_url,
                hts_endpoint=remote_client.hts_endpoint,
                **(request_kwargs or {}),
            ).gen_url()
            cached_xml = remote_client.session.get(cached_url).text
            path.write_text(cached_xml, encoding="utf-8")
        raw_xml = path.read_text(encoding="utf-8")
        return raw_xml

    return fixture_func


def create_mocked_fixtures(filename: str):
    """Factory to create mocked fixtures."""

    @pytest.fixture
    def fixture_func():
        """Load test XML once per test session."""
        from pathlib import Path

        path = (
            Path(__file__).parent.parent.parent / "mocked_data" / "get_data" / filename
        )
        raw_xml = path.read_text(encoding="utf-8")
        return raw_xml

    return fixture_func


# Create cached fixtures
basic_response_xml_cached = create_cached_fixtures(
    "basic_response.xml",
    {
        "site": os.getenv("TEST_SITE"),
        "measurement": os.getenv("TEST_MEASUREMENT"),
        "from_datetime": "2023-01-01T00:00:00",
        "to_datetime": "2023-02-01T00:00:00",
    },
)
one_point_response_xml_cached = create_cached_fixtures(
    "one_point_response.xml",
    {
        "site": os.getenv("TEST_SITE"),
        "measurement": os.getenv("TEST_MEASUREMENT"),
    },
)
collection_response_xml_cached = create_cached_fixtures(
    "collection_response.xml",
    {
        "site": os.getenv("TEST_SITE"),
        "measurement": os.getenv("TEST_MEASUREMENT"),
        "collection": os.getenv("TEST_COLLECTION"),
        "from_datetime": "2023-01-01T00:00:00",
        "to_datetime": "2023-02-01T00:00:00",
    },
)
time_interval_response_xml_cached = create_cached_fixtures(
    "time_interval_response.xml",
    {
        "site": os.getenv("TEST_SITE"),
        "measurement": os.getenv("TEST_MEASUREMENT"),
        "time_interval": "2023-01-01T12:00:00/2023-01-02T12:00:00",
    },
)
time_interval_complex_response_xml_cached = create_cached_fixtures(
    "time_interval_response.xml",
    {
        "site": os.getenv("TEST_SITE"),
        "measurement": os.getenv("TEST_MEASUREMENT"),
        "time_interval": "2023-01-01T12:00:00/P2DT2H",  # 2 days
        "alignment": "3h",
    },
)
date_only_response_xml_cached = create_cached_fixtures(
    "date_only_response.xml",
    {
        "site": os.getenv("TEST_SITE"),
        "measurement": os.getenv("TEST_MEASUREMENT"),
        "time_interval": "2023-01-01T12:00:00/P2DT2H",  # 2 days
        "date_only": "Yes",
    },
)

# Create mocked fixtures
basic_response_xml_mocked = create_mocked_fixtures("basic_response.xml")
one_point_response_xml_mocked = create_mocked_fixtures("one_point_response.xml")
collection_response_xml_mocked = create_mocked_fixtures("collection_response.xml")
time_interval_response_xml_mocked = create_mocked_fixtures("time_interval_response.xml")
time_interval_complex_response_xml_mocked = create_mocked_fixtures(
    "time_interval_complex_response.xml"
)
date_only_response_xml_mocked = create_mocked_fixtures("date_only_response.xml")


class TestRemoteFixtures:
    @pytest.mark.remote
    @pytest.mark.update
    def test_basic_response_xml_fixture(
        self, remote_client, httpx_mock, basic_response_xml_cached
    ):
        """Test the basic_response_xml_cached fixture."""

        from urllib.parse import urlparse

        from hurl.schemas.requests import GetDataRequest
        from tests.conftest import remove_tags

        # Get the remote URL
        remote_url = GetDataRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            site=os.getenv("TEST_SITE"),
            measurement=os.getenv("TEST_MEASUREMENT"),
            from_datetime="2023-01-01T00:00:00",
            to_datetime="2023-02-01T00:00:00",
        ).gen_url()

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        # Get the remote XML
        remote_xml = remote_client.session.get(remote_url).text

        # remove the time tags (will change often)
        remote_xml_cleaned = remove_tags(remote_xml, ["T", "E"])
        basic_response_xml_cleaned = remove_tags(basic_response_xml_cached, ["T", "E"])

        # Compare the local and remote XML
        assert basic_response_xml_cleaned == remote_xml_cleaned

    @pytest.mark.remote
    @pytest.mark.update
    def test_one_point_response_xml_fixture(
        self, remote_client, httpx_mock, one_point_response_xml_cached
    ):
        """Test the one_point_response_xml fixture."""

        from urllib.parse import urlparse

        from hurl.schemas.requests import GetDataRequest
        from tests.conftest import remove_tags

        # Get the remote URL
        remote_url = GetDataRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            site=os.getenv("TEST_SITE"),
            measurement=os.getenv("TEST_MEASUREMENT"),
        ).gen_url()

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        # Get the remote XML
        remote_xml = remote_client.session.get(remote_url).text

        # remove the time tags (will change often)
        remote_xml_cleaned = remove_tags(remote_xml, ["T", "E"])
        one_point_response_xml_cleaned = remove_tags(
            one_point_response_xml_cached, ["T", "E"]
        )

        # Compare the local and remote XML
        assert one_point_response_xml_cleaned == remote_xml_cleaned

    @pytest.mark.remote
    @pytest.mark.update
    def test_collection_response_xml_fixture(
        self, remote_client, httpx_mock, collection_response_xml_cached
    ):
        """Test the collection_response_xml fixture."""

        from urllib.parse import urlparse

        import pandas as pd

        from hurl.schemas.requests import GetDataRequest
        from tests.conftest import remove_tags

        # 12 hours ago from now
        start_time = pd.Timestamp.now() - pd.Timedelta(hours=48)
        # ... in format YYYY-MM-DDTHH:MM:SS
        start_timestamp = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        # Get the remote URL
        remote_url = GetDataRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            collection=os.getenv("TEST_COLLECTION"),
            from_datetime="2023-01-01T00:00:00",
            to_datetime="2023-02-01T00:00:00",
        ).gen_url()

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        # Get the remote XML
        remote_xml = remote_client.session.get(remote_url).text

        # remove the time tags (will change often)
        remote_xml_cleaned = remove_tags(remote_xml, ["T", "E"])
        collection_response_xml_cleaned = remove_tags(
            collection_response_xml_cached, ["T", "E"]
        )

        # Compare the local and remote XML
        assert collection_response_xml_cleaned == remote_xml_cleaned

    @pytest.mark.remote
    @pytest.mark.update
    def test_time_interval_response_xml_fixture(
        self, remote_client, httpx_mock, time_interval_response_xml_cached
    ):
        """Test the time_interval_response_xml fixture."""

        from urllib.parse import urlparse

        from hurl.schemas.requests import GetDataRequest
        from tests.conftest import remove_tags

        # Get the remote URL
        remote_url = GetDataRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            site=os.getenv("TEST_SITE"),
            measurement=os.getenv("TEST_MEASUREMENT"),
            time_interval="2023-01-01T12:00:00/2023-01-02T12:00:00",
        ).gen_url()

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        # Get the remote XML
        remote_xml = remote_client.session.get(remote_url).text

        # remove the time tags (will change often)
        remote_xml_cleaned = remove_tags(remote_xml, ["T", "E"])
        time_interval_response_xml_cleaned = remove_tags(
            time_interval_response_xml_cached, ["T", "E"]
        )

        # Compare the local and remote XML
        assert time_interval_response_xml_cleaned == remote_xml_cleaned

    @pytest.mark.remote
    @pytest.mark.update
    def test_time_interval_complex_response_xml_fixture(
        self, remote_client, httpx_mock, time_interval_complex_response_xml_cached
    ):
        """Test the time_interval_response_xml fixture."""

        from urllib.parse import urlparse

        from hurl.schemas.requests import GetDataRequest
        from tests.conftest import remove_tags

        # Get the remote URL
        remote_url = GetDataRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            site=os.getenv("TEST_SITE"),
            measurement=os.getenv("TEST_MEASUREMENT"),
            time_interval="2023-01-01T12:00:00/P2DT2H",  # 2 days, 2 hours
            alignment="3h",  # Align to 3 hour intervals
        ).gen_url()

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        # Get the remote XML
        remote_xml = remote_client.session.get(remote_url).text

        # remove the time tags (will change often)
        remote_xml_cleaned = remove_tags(remote_xml, ["T", "E"])
        time_interval_complex_response_xml_cleaned = remove_tags(
            time_interval_complex_response_xml_cached, ["T", "E"]
        )

        # Compare the local and remote XML
        assert time_interval_complex_response_xml_cleaned == remote_xml_cleaned

    @pytest.mark.remote
    @pytest.mark.update
    def test_date_only_response_xml_fixture(
        self, remote_client, httpx_mock, date_only_response_xml_cached
    ):
        """Test the time_interval_response_xml fixture."""

        from urllib.parse import urlparse

        from hurl.schemas.requests import GetDataRequest

        # Get the remote URL
        remote_url = GetDataRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            site=os.getenv("TEST_SITE"),
            measurement=os.getenv("TEST_MEASUREMENT"),
            time_interval="2023-01-01T12:00:00/P2DT2H",  # 2 days, 2 hours
            date_only="Yes",
        ).gen_url()

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        # Get the remote XML
        remote_xml = remote_client.session.get(remote_url).text

        # Compare the local and remote XML
        assert date_only_response_xml_cached == remote_xml


class TestResponseValidation:

    @pytest.mark.unit
    def test_basic_response_xml_unit(self, httpx_mock, basic_response_xml_mocked):
        """Test basic xml response method with mocked data."""

        import pandas as pd

        from hurl.client import HilltopClient
        from hurl.schemas.requests import GetDataRequest
        from hurl.schemas.responses import GetDataResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        # This is a reconstruction of the url that would be generated by the client
        test_url = GetDataRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site="Test Site Alpha",
            measurement="Stage",
            from_datetime="2023-01-01T00:00:00",
            to_datetime="2023-02-01T00:00:00",
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=basic_response_xml_mocked,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            result = client.get_data(
                site="Test Site Alpha",
                measurement="Stage",
                from_datetime="2023-01-01T00:00:00",
                to_datetime="2023-02-01T00:00:00",
            )

        # Base Model
        assert isinstance(result, GetDataResponse)
        assert result.agency == "Test Council"

        # Measurement
        assert len(result.measurement) == 1
        measurement = result.measurement[0]
        assert isinstance(measurement, GetDataResponse.Measurement)
        assert measurement.site_name == "Test Site Alpha"

        # Data Source
        data_source = measurement.data_source
        assert isinstance(data_source, GetDataResponse.Measurement.DataSource)
        assert data_source.name == "Water Level"
        assert data_source.num_items == 1
        assert data_source.ts_type == "StdSeries"
        assert data_source.data_type == "SimpleTimeSeries"
        assert data_source.interpolation == "Instant"
        assert data_source.item_format is None

        # Item Info
        assert len(data_source.item_info) == 1
        item_info = data_source.item_info[0]
        assert isinstance(item_info, GetDataResponse.Measurement.DataSource.ItemInfo)
        assert item_info.item_number == 1
        assert item_info.item_name == "Stage"
        assert item_info.item_format == "F"
        assert item_info.units == "mm"
        assert item_info.format == "####"

        # Data
        data = measurement.data
        assert isinstance(data, GetDataResponse.Measurement.Data)
        assert data.date_format == "Calendar"
        assert data.num_items == 1

        assert isinstance(data.timeseries, pd.DataFrame)
        assert len(data.timeseries) > 0
        assert data.timeseries.index.name == "DateTime"
        assert "Stage" in data.timeseries.columns
        assert data.timeseries.index.dtype == "datetime64[ns]"

        # Check dataframe conversion
        df = result.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    @pytest.mark.integration
    def test_basic_response_xml_integration(
        self, httpx_mock, basic_response_xml_cached
    ):
        """Test basic xml response method."""

        import pandas as pd

        from hurl.client import HilltopClient
        from hurl.schemas.requests import GetDataRequest
        from hurl.schemas.responses import GetDataResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        # This is a reconstruction of the url that would be generated by the client
        test_url = GetDataRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site=os.getenv("TEST_SITE"),
            measurement=os.getenv("TEST_MEASUREMENT"),
            from_datetime="2023-01-01T00:00:00",
            to_datetime="2023-01-02T00:00:00",
        ).gen_url()

        # Here we tell httpx_mock to expect a GET request to the test_url, and
        # to return the basic_response_xml as the response.
        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=basic_response_xml_cached,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:

            result = client.get_data(
                site=os.getenv("TEST_SITE"),
                measurement=os.getenv("TEST_MEASUREMENT"),
                from_datetime="2023-01-01T00:00:00",
                to_datetime="2023-01-02T00:00:00",
            )

        # Base Model
        assert isinstance(result, GetDataResponse)
        assert result.agency == os.getenv("TEST_AGENCY")

        # Measurement
        assert len(result.measurement) == 1
        measurement = result.measurement[0]
        assert isinstance(measurement, GetDataResponse.Measurement)
        assert measurement.site_name == os.getenv("TEST_SITE")

        # Data Source
        data_source = measurement.data_source
        assert isinstance(data_source, GetDataResponse.Measurement.DataSource)

        # Item Info
        assert len(data_source.item_info) == 1
        item_info = data_source.item_info[0]
        assert isinstance(item_info, GetDataResponse.Measurement.DataSource.ItemInfo)
        assert item_info.item_number == 1
        assert item_info.item_name == os.getenv("TEST_MEASUREMENT")

        # Data
        data = measurement.data
        assert isinstance(data, GetDataResponse.Measurement.Data)
        assert data.date_format == "Calendar"

        assert isinstance(data.timeseries, pd.DataFrame)
        assert len(data.timeseries) > 0
        assert data.timeseries.index.name == "DateTime"
        assert os.getenv("TEST_MEASUREMENT") in data.timeseries.columns
        assert data.timeseries.index.dtype == "datetime64[ns]"

    @pytest.mark.unit
    def test_collection_response_xml_unit(
        self, httpx_mock, collection_response_xml_mocked
    ):
        """Test collection response."""

        import pandas as pd

        from hurl.client import HilltopClient
        from hurl.schemas.requests import GetDataRequest
        from hurl.schemas.responses import GetDataResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        start_time = pd.Timestamp.now() - pd.Timedelta(hours=48)
        # ... in format YYYY-MM-DDTHH:MM:SS
        start_timestamp = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        # This is a reconstruction of the url that would be generated by the client
        test_url = GetDataRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            collection="Rainfall",
            from_datetime=start_timestamp,
        ).gen_url()

        # Here we tell httpx_mock to expect a GET request to the test_url, and
        # to return the collection_response_xml as the response.
        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=collection_response_xml_mocked,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:

            result = client.get_data(
                collection="Rainfall",
                from_datetime=start_timestamp,
            )

        # Test the top level response object
        assert isinstance(result, GetDataResponse)
        assert result.agency == "Test Council"

        assert len(result.measurement) > 0
        assert isinstance(result.measurement, list)

        # Find the measurement with the site_name "Kahuterawa at Scotts Road"
        measurement = next(
            (m for m in result.measurement if m.site_name == "Test Site Alpha"),
            None,
        )
        assert isinstance(measurement, GetDataResponse.Measurement)
        assert isinstance(
            measurement.data_source, GetDataResponse.Measurement.DataSource
        )

        # Test the data source
        data_source = measurement.data_source
        assert data_source.name == "Water Level"
        assert data_source.num_items == 1
        assert data_source.ts_type == "StdSeries"
        assert data_source.data_type == "SimpleTimeSeries"
        assert data_source.interpolation == "Instant"
        assert data_source.item_format is None
        assert len(data_source.item_info) == 1

        # Test the item info
        item_info = data_source.item_info[0]
        assert isinstance(item_info, GetDataResponse.Measurement.DataSource.ItemInfo)
        assert item_info.item_number == 1
        assert item_info.item_name == "Stage"
        assert item_info.item_format == "F"
        assert item_info.divisor is None
        assert item_info.units == "mm"
        assert item_info.format == "####"

        # Test the data
        data = measurement.data
        assert isinstance(data, GetDataResponse.Measurement.Data)
        assert data.date_format == "Calendar"
        assert data.num_items == 1
        assert isinstance(data.timeseries, pd.DataFrame)
        assert len(data.timeseries) > 0

        # Test the timeseries DataFrame
        assert data.timeseries.index.name == "DateTime"
        assert "Stage" in data.timeseries.columns
        assert data.timeseries.index.dtype == "datetime64[ns]"

    @pytest.mark.integration
    def test_collection_response_xml_integration(
        self, httpx_mock, collection_response_xml_cached
    ):
        """Test collection response."""

        import pandas as pd

        from hurl.client import HilltopClient
        from hurl.schemas.requests import GetDataRequest
        from hurl.schemas.responses import GetDataResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        # This is a reconstruction of the url that would be generated by the client
        test_url = GetDataRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            collection=os.getenv("TEST_COLLECTION"),
            from_datetime="2023-01-01T00:00:00",
            to_datetime="2023-02-01T00:00:00",
        ).gen_url()

        # Here we tell httpx_mock to expect a GET request to the test_url, and
        # to return the collection_response_xml as the response.
        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=collection_response_xml_cached,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:

            result = client.get_data(
                collection=os.getenv("TEST_COLLECTION"),
                from_datetime="2023-01-01T00:00:00",
                to_datetime="2023-02-01T00:00:00",
            )

        # Test the top level response object
        assert isinstance(result, GetDataResponse)
        assert result.agency == os.getenv("TEST_AGENCY")

        assert len(result.measurement) > 0
        assert isinstance(result.measurement, list)

        # Find the measurement with the site_name "Kahuterawa at Scotts Road"
        measurement = next(
            (m for m in result.measurement if m.site_name == os.getenv("TEST_SITE")),
            None,
        )
        assert isinstance(measurement, GetDataResponse.Measurement)
        assert isinstance(
            measurement.data_source, GetDataResponse.Measurement.DataSource
        )

        # Test the data source
        data_source = measurement.data_source
        assert data_source.name == os.getenv("TEST_DATA_SOURCE")

        # Test the item info
        item_info = data_source.item_info[0]
        assert isinstance(item_info, GetDataResponse.Measurement.DataSource.ItemInfo)
        assert item_info.item_name == os.getenv("TEST_MEASUREMENT")

        # Test the data
        data = measurement.data
        assert isinstance(data, GetDataResponse.Measurement.Data)
        assert data.date_format == "Calendar"
        assert data.num_items == 1
        assert isinstance(data.timeseries, pd.DataFrame)
        assert len(data.timeseries) > 0

        # Test the timeseries DataFrame
        assert data.timeseries.index.name == "DateTime"
        assert os.getenv("TEST_MEASUREMENT") in data.timeseries.columns
        assert data.timeseries.index.dtype == "datetime64[ns]"

    @pytest.mark.unit
    def test_one_point_response_xml_unit(
        self, httpx_mock, one_point_response_xml_mocked
    ):
        """Test single point response."""

        import pandas as pd

        from hurl.client import HilltopClient
        from hurl.schemas.requests import GetDataRequest
        from hurl.schemas.responses import GetDataResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        # This is a reconstruction of the url that would be generated by the client
        test_url = GetDataRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site="Test Site Alpha",
            measurement="Stage",
        ).gen_url()

        # Here we tell httpx_mock to expect a GET request to the test_url, and
        # to return the one_point_response_xml as the response.
        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=one_point_response_xml_mocked,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:

            result = client.get_data(
                site="Test Site Alpha",
                measurement="Stage",
            )

        # Test the top level response object
        assert isinstance(result, GetDataResponse)
        assert result.agency == "Test Council"

        assert len(result.measurement) > 0
        assert isinstance(result.measurement, list)

        # Find the measurement with the site_name os.getenv("TEST_SITE")
        measurement = next(
            (m for m in result.measurement if m.site_name == "Test Site Alpha"),
            None,
        )
        assert isinstance(measurement, GetDataResponse.Measurement)
        assert isinstance(
            measurement.data_source, GetDataResponse.Measurement.DataSource
        )

        # Test the data source
        data_source = measurement.data_source
        assert data_source.name == "Water Level"
        assert data_source.num_items == 1
        assert data_source.ts_type == "StdSeries"
        assert data_source.data_type == "SimpleTimeSeries"
        assert data_source.interpolation == "Instant"
        assert data_source.item_format is None
        assert len(data_source.item_info) == 1

        # Test the item info
        item_info = data_source.item_info[0]
        assert isinstance(item_info, GetDataResponse.Measurement.DataSource.ItemInfo)
        assert item_info.item_number == 1
        assert item_info.item_name == "Stage"
        assert item_info.item_format == "F"
        assert item_info.divisor is None
        assert item_info.units == "mm"
        assert item_info.format == "####"

        # Test the data
        data = measurement.data
        assert isinstance(data, GetDataResponse.Measurement.Data)
        assert data.date_format == "Calendar"
        assert data.num_items == 1
        assert isinstance(data.timeseries, pd.DataFrame)
        assert len(data.timeseries) == 1

        # Test the timeseries DataFrame
        assert data.timeseries.index.name == "DateTime"
        assert "Stage" in data.timeseries.columns
        assert data.timeseries.index.dtype == "datetime64[ns]"

    @pytest.mark.integration
    def test_one_point_response_xml_integration(
        self, httpx_mock, one_point_response_xml_cached
    ):
        """Test single point response."""

        import pandas as pd

        from hurl.client import HilltopClient
        from hurl.schemas.requests import GetDataRequest
        from hurl.schemas.responses import GetDataResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        # This is a reconstruction of the url that would be generated by the client
        test_url = GetDataRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site=os.getenv("TEST_SITE"),
            measurement=os.getenv("TEST_MEASUREMENT"),
        ).gen_url()

        # Here we tell httpx_mock to expect a GET request to the test_url, and
        # to return the one_point_response_xml as the response.
        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=one_point_response_xml_cached,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:

            result = client.get_data(
                site=os.getenv("TEST_SITE"),
                measurement=os.getenv("TEST_MEASUREMENT"),
            )

        # Test the top level response object
        assert isinstance(result, GetDataResponse)
        assert result.agency == os.getenv("TEST_AGENCY")

        assert len(result.measurement) > 0
        assert isinstance(result.measurement, list)

        # Find the measurement with the site_name os.getenv("TEST_SITE")
        measurement = next(
            (m for m in result.measurement if m.site_name == os.getenv("TEST_SITE")),
            None,
        )
        assert isinstance(measurement, GetDataResponse.Measurement)
        assert isinstance(
            measurement.data_source, GetDataResponse.Measurement.DataSource
        )

        # Test the data source
        data_source = measurement.data_source
        assert data_source.name == os.getenv("TEST_DATA_SOURCE")

        # Test the item info
        item_info = data_source.item_info[0]
        assert isinstance(item_info, GetDataResponse.Measurement.DataSource.ItemInfo)
        assert item_info.item_name == os.getenv("TEST_MEASUREMENT")

        # Test the data
        data = measurement.data
        assert isinstance(data, GetDataResponse.Measurement.Data)
        assert data.date_format == "Calendar"
        assert isinstance(data.timeseries, pd.DataFrame)

        # Test the timeseries DataFrame
        assert data.timeseries.index.name == "DateTime"
        assert os.getenv("TEST_MEASUREMENT") in data.timeseries.columns
        assert data.timeseries.index.dtype == "datetime64[ns]"

    @pytest.mark.unit
    def test_time_interval_response_xml_unit(
        self, httpx_mock, time_interval_response_xml_mocked
    ):
        """Test time interval point response."""

        import pandas as pd

        from hurl.client import HilltopClient
        from hurl.schemas.requests import GetDataRequest
        from hurl.schemas.responses import GetDataResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        time_interval = "2023-01-01T12:00:00/2023-01-02T12:00:00"

        # This is a reconstruction of the url that would be generated by the client
        test_url = GetDataRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site="Test Site Alpha",
            measurement="Stage",
            time_interval=time_interval,
        ).gen_url()

        # Here we tell httpx_mock to expect a GET request to the test_url, and
        # to return the one_point_response_xml as the response.
        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=time_interval_response_xml_mocked,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:

            result = client.get_data(
                site="Test Site Alpha",
                measurement="Stage",
                time_interval=time_interval,
            )

        # Test the top level response object
        assert isinstance(result, GetDataResponse)
        assert result.agency == "Test Council"

        assert len(result.measurement) > 0
        assert isinstance(result.measurement, list)

        # Find the measurement with the site_name os.getenv("TEST_SITE")
        measurement = next(
            (m for m in result.measurement if m.site_name == "Test Site Alpha"),
            None,
        )
        assert isinstance(measurement, GetDataResponse.Measurement)
        assert isinstance(
            measurement.data_source, GetDataResponse.Measurement.DataSource
        )

        # Test the data source
        data_source = measurement.data_source
        assert data_source.name == "Water Level"
        assert data_source.num_items == 1
        assert data_source.ts_type == "StdSeries"
        assert data_source.data_type == "SimpleTimeSeries"
        assert data_source.interpolation == "Instant"
        assert data_source.item_format is None
        assert len(data_source.item_info) == 1

        # Test the item info
        item_info = data_source.item_info[0]
        assert isinstance(item_info, GetDataResponse.Measurement.DataSource.ItemInfo)
        assert item_info.item_number == 1
        assert item_info.item_name == "Stage"
        assert item_info.item_format == "F"
        assert item_info.divisor is None
        assert item_info.units == "mm"
        assert item_info.format == "####"

        # Test the data
        data = measurement.data
        assert isinstance(data, GetDataResponse.Measurement.Data)
        assert data.date_format == "Calendar"
        assert data.num_items == 1
        assert isinstance(data.timeseries, pd.DataFrame)
        assert len(data.timeseries) >= 1

        # Test the timeseries DataFrame
        assert data.timeseries.index.name == "DateTime"
        assert "Stage" in data.timeseries.columns
        assert data.timeseries.index.dtype == "datetime64[ns]"

    @pytest.mark.integration
    def test_time_interval_response_xml_integration(
        self, httpx_mock, time_interval_response_xml_cached
    ):
        """Test time interval point response."""

        import pandas as pd

        from hurl.client import HilltopClient
        from hurl.schemas.requests import GetDataRequest
        from hurl.schemas.responses import GetDataResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        time_interval = "2023-01-01T12:00:00/2023-01-02T12:00:00"

        # This is a reconstruction of the url that would be generated by the client
        test_url = GetDataRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site=os.getenv("TEST_SITE"),
            measurement=os.getenv("TEST_MEASUREMENT"),
            time_interval=time_interval,
        ).gen_url()

        # Here we tell httpx_mock to expect a GET request to the test_url, and
        # to return the one_point_response_xml as the response.
        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=time_interval_response_xml_cached,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:

            result = client.get_data(
                site=os.getenv("TEST_SITE"),
                measurement=os.getenv("TEST_MEASUREMENT"),
                time_interval=time_interval,
            )

        # Test the top level response object
        assert isinstance(result, GetDataResponse)
        assert result.agency == os.getenv("TEST_AGENCY")

        assert len(result.measurement) > 0
        assert isinstance(result.measurement, list)

        # Find the measurement with the site_name os.getenv("TEST_SITE")
        measurement = next(
            (m for m in result.measurement if m.site_name == os.getenv("TEST_SITE")),
            None,
        )
        assert isinstance(measurement, GetDataResponse.Measurement)
        assert isinstance(
            measurement.data_source, GetDataResponse.Measurement.DataSource
        )

        # Test the data source
        data_source = measurement.data_source
        assert data_source.name == os.getenv("TEST_DATA_SOURCE")

        # Test the item info
        item_info = data_source.item_info[0]
        assert isinstance(item_info, GetDataResponse.Measurement.DataSource.ItemInfo)
        assert item_info.item_name == os.getenv("TEST_MEASUREMENT")

        # Test the data
        data = measurement.data
        assert isinstance(data, GetDataResponse.Measurement.Data)
        assert data.date_format == "Calendar"
        assert isinstance(data.timeseries, pd.DataFrame)

        # Test the timeseries DataFrame
        assert data.timeseries.index.name == "DateTime"
        assert os.getenv("TEST_MEASUREMENT") in data.timeseries.columns
        assert data.timeseries.index.dtype == "datetime64[ns]"

    @pytest.mark.unit
    def test_time_interval_complex_response_xml_unit(
        self, httpx_mock, time_interval_complex_response_xml_mocked
    ):
        """Test time interval point response."""

        import pandas as pd

        from hurl.client import HilltopClient
        from hurl.schemas.requests import GetDataRequest
        from hurl.schemas.responses import GetDataResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        time_interval = "2023-01-01T12:00:00/P2DT2H"  # 2 days 2 hours
        alignment = "3h"  # Align to 3 hour intervals

        # This is a reconstruction of the url that would be generated by the client
        test_url = GetDataRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site="Test Site Alpha",
            measurement="Stage",
            time_interval=time_interval,
            alignment=alignment,
        ).gen_url()

        # Here we tell httpx_mock to expect a GET request to the test_url, and
        # to return the one_point_response_xml as the response.
        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=time_interval_complex_response_xml_mocked,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:

            result = client.get_data(
                site="Test Site Alpha",
                measurement="Stage",
                time_interval=time_interval,
                alignment=alignment,
            )

        # Test the top level response object
        assert isinstance(result, GetDataResponse)
        assert result.agency == "Test Council"

        assert len(result.measurement) > 0
        assert isinstance(result.measurement, list)

        # Find the measurement with the site_name os.getenv("TEST_SITE")
        measurement = next(
            (m for m in result.measurement if m.site_name == "Test Site Alpha"),
            None,
        )
        assert isinstance(measurement, GetDataResponse.Measurement)
        assert isinstance(
            measurement.data_source, GetDataResponse.Measurement.DataSource
        )

        # Test the data source
        data_source = measurement.data_source
        assert data_source.name == "Water Level"
        assert data_source.num_items == 1
        assert data_source.ts_type == "StdSeries"
        assert data_source.data_type == "SimpleTimeSeries"
        assert data_source.interpolation == "Instant"
        assert data_source.item_format is None
        assert len(data_source.item_info) == 1

        # Test the item info
        item_info = data_source.item_info[0]
        assert isinstance(item_info, GetDataResponse.Measurement.DataSource.ItemInfo)
        assert item_info.item_number == 1
        assert item_info.item_name == "Stage"
        assert item_info.item_format == "F"
        assert item_info.divisor is None
        assert item_info.units == "mm"
        assert item_info.format == "####"

        # Test the data
        data = measurement.data
        assert isinstance(data, GetDataResponse.Measurement.Data)
        assert data.date_format == "Calendar"
        assert data.num_items == 1
        assert isinstance(data.timeseries, pd.DataFrame)
        assert len(data.timeseries) >= 1

        # Test the timeseries DataFrame
        assert data.timeseries.index.name == "DateTime"
        assert "Stage" in data.timeseries.columns
        assert data.timeseries.index.dtype == "datetime64[ns]"

        # Check that the timeseries starts at the expected time
        expected_start_time = pd.Timestamp("2023-01-01T12:00:00")
        assert data.timeseries.index[0] == expected_start_time

        # Check that the timeseries ends at the expected time
        assert data.timeseries.index[-1] == expected_start_time + pd.Timedelta(
            days=2, hours=2
        )

    @pytest.mark.integration
    def test_time_interval_complex_response_xml_integration(
        self, httpx_mock, time_interval_complex_response_xml_cached
    ):
        """Test time interval point response."""

        import pandas as pd

        from hurl.client import HilltopClient
        from hurl.schemas.requests import GetDataRequest
        from hurl.schemas.responses import GetDataResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        time_interval = "2023-01-01T12:00:00/P2DT2H"  # 2 days 2 hours
        alignment = "3h"  # Align to 3 hour intervals

        # This is a reconstruction of the url that would be generated by the client
        test_url = GetDataRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site=os.getenv("TEST_SITE"),
            measurement=os.getenv("TEST_MEASUREMENT"),
            time_interval=time_interval,
            alignment=alignment,
        ).gen_url()

        # Here we tell httpx_mock to expect a GET request to the test_url, and
        # to return the one_point_response_xml as the response.
        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=time_interval_complex_response_xml_cached,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:

            result = client.get_data(
                site=os.getenv("TEST_SITE"),
                measurement=os.getenv("TEST_MEASUREMENT"),
                time_interval=time_interval,
                alignment=alignment,
            )

        # Test the top level response object
        assert isinstance(result, GetDataResponse)
        assert result.agency == os.getenv("TEST_AGENCY")

        assert len(result.measurement) > 0
        assert isinstance(result.measurement, list)

        # Find the measurement with the site_name os.getenv("TEST_SITE")
        measurement = next(
            (m for m in result.measurement if m.site_name == os.getenv("TEST_SITE")),
            None,
        )
        assert isinstance(measurement, GetDataResponse.Measurement)
        assert isinstance(
            measurement.data_source, GetDataResponse.Measurement.DataSource
        )

        # Test the data source
        data_source = measurement.data_source
        assert data_source.name == os.getenv("TEST_DATA_SOURCE")

        # Test the item info
        item_info = data_source.item_info[0]
        assert isinstance(item_info, GetDataResponse.Measurement.DataSource.ItemInfo)
        assert item_info.item_name == os.getenv("TEST_MEASUREMENT")

        # Test the data
        data = measurement.data
        assert isinstance(data, GetDataResponse.Measurement.Data)
        assert data.date_format == "Calendar"
        assert data.num_items == 1
        assert isinstance(data.timeseries, pd.DataFrame)
        assert len(data.timeseries) >= 1

        # Test the timeseries DataFrame
        assert data.timeseries.index.name == "DateTime"
        assert os.getenv("TEST_MEASUREMENT") in data.timeseries.columns
        assert data.timeseries.index.dtype == "datetime64[ns]"

        # Check that the timeseries starts at the expected time
        expected_start_time = pd.Timestamp("2023-01-01T12:00:00")
        assert data.timeseries.index[0] == expected_start_time

        # Check that the timeseries ends at the expected time
        assert data.timeseries.index[-1] == expected_start_time + pd.Timedelta(
            days=2, hours=2
        )
