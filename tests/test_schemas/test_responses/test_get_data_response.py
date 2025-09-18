import pytest


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
            Path(__file__).parent.parent.parent
            / "mocked_data"
            / "get_data"
            / filename
        )
        raw_xml = path.read_text(encoding="utf-8")
        return raw_xml
    return fixture_func


# Create cached fixtures
basic_response_xml_cached = create_cached_fixtures("basic_response.xml", {
    "site": "Manawatu at Teachers College",
    "measurement": "Stage",
    "from_datetime": "2023-01-01T00:00:00",
    "to_datetime": "2023-02-01T00:00:00"
})

# Create mocked fixtures
basic_response_xml_mocked = create_mocked_fixtures("basic_response.xml")


# Keep existing fixtures for now to avoid breaking everything


@pytest.fixture
def basic_response_xml(request, httpx_mock, remote_client):
    """Fixture to get a single point response XML for testing."""
    from pathlib import Path
    from urllib.parse import urlparse

    from hurl.schemas.requests import GetDataRequest

    path = (
        Path(__file__).parent.parent.parent
        / "fixture_cache"
        / "get_data"
        / "basic_response.xml"
    )

    if request.config.getoption("--update"):

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        remote_url = GetDataRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            site="Manawatu at Teachers College",
            measurement="Stage",
            from_datetime="2023-01-01T00:00:00",
            to_datetime="2023-02-01T00:00:00",
        ).gen_url()
        remote_xml = remote_client.session.get(remote_url).text

        path.write_text(remote_xml, encoding="utf-8")

    raw_xml = path.read_text(encoding="utf-8")

    return raw_xml


@pytest.fixture
def collection_response_xml(request, httpx_mock, remote_client):
    """Fixture to get a single point response XML for testing."""
    from pathlib import Path
    from urllib.parse import urlparse

    import pandas as pd

    from hurl.schemas.requests import GetDataRequest

    path = (
        Path(__file__).parent.parent.parent
        / "fixture_cache"
        / "get_data"
        / "collection_response.xml"
    )

    if request.config.getoption("--update"):

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        # 12 hours ago from now
        start_time = pd.Timestamp.now() - pd.Timedelta(hours=48)
        # ... in format YYYY-MM-DDTHH:MM:SS
        start_timestamp = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        remote_url = GetDataRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            collection="Rainfall",
            from_datetime=start_timestamp,
        ).gen_url()
        remote_xml = remote_client.session.get(remote_url).text

        path.write_text(remote_xml, encoding="utf-8")

    raw_xml = path.read_text(encoding="utf-8")

    return raw_xml


@pytest.fixture
def one_point_response_xml(request, httpx_mock, remote_client):
    """Fixture to get a single point response XML for testing."""
    from pathlib import Path
    from urllib.parse import urlparse

    from hurl.schemas.requests import GetDataRequest

    path = (
        Path(__file__).parent.parent.parent
        / "fixture_cache"
        / "get_data"
        / "one_point_response.xml"
    )

    if request.config.getoption("--update"):

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        remote_url = GetDataRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            site="Manawatu at Teachers College",
            measurement="Stage",
        ).gen_url()
        remote_xml = remote_client.session.get(remote_url).text

        path.write_text(remote_xml, encoding="utf-8")

    raw_xml = path.read_text(encoding="utf-8")

    return raw_xml


@pytest.fixture
def time_interval_response_xml(request, httpx_mock, remote_client):
    """Fixture to get a single point response XML for testing."""
    from pathlib import Path
    from urllib.parse import urlparse

    from hurl.schemas.requests import GetDataRequest

    path = (
        Path(__file__).parent.parent.parent
        / "fixture_cache"
        / "get_data"
        / "time_interval_response.xml"
    )

    if request.config.getoption("--update"):

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        remote_url = GetDataRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            site="Manawatu at Teachers College",
            measurement="Stage",
            time_interval="2023-01-01T12:00:00/2023-01-02T12:00:00",
        ).gen_url()
        remote_xml = remote_client.session.get(remote_url).text

        path.write_text(remote_xml, encoding="utf-8")

    raw_xml = path.read_text(encoding="utf-8")

    return raw_xml


@pytest.fixture
def time_interval_complex_response_xml(request, httpx_mock, remote_client):
    """Fixture to get a single point response XML for testing."""
    from pathlib import Path
    from urllib.parse import urlparse

    from hurl.schemas.requests import GetDataRequest

    path = (
        Path(__file__).parent.parent.parent
        / "fixture_cache"
        / "get_data"
        / "time_interval_complex_response.xml"
    )

    if request.config.getoption("--update"):

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        remote_url = GetDataRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            site="Manawatu at Teachers College",
            measurement="Stage",
            time_interval="2023-01-01T12:00:00/P2DT2H",  # 2 days
            alignment="3h",
        ).gen_url()
        remote_xml = remote_client.session.get(remote_url).text

        path.write_text(remote_xml, encoding="utf-8")

    raw_xml = path.read_text(encoding="utf-8")

    return raw_xml


@pytest.fixture
def date_only_response_xml(request, httpx_mock, remote_client):
    """Fixture to get a single point response XML for testing."""
    from pathlib import Path
    from urllib.parse import urlparse

    from hurl.schemas.requests import GetDataRequest

    path = (
        Path(__file__).parent.parent.parent
        / "fixture_cache"
        / "get_data"
        / "date_only_response.xml"
    )

    if request.config.getoption("--update"):

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        remote_url = GetDataRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            site="Manawatu at Teachers College",
            measurement="Stage",
            time_interval="2023-01-01T12:00:00/P2DT2H",  # 2 days
            date_only="Yes",
        ).gen_url()
        remote_xml = remote_client.session.get(remote_url).text

        path.write_text(remote_xml, encoding="utf-8")

    raw_xml = path.read_text(encoding="utf-8")

    return raw_xml


class TestRemoteFixtures:
    @pytest.mark.remote
    @pytest.mark.update
    def test_basic_response_xml_fixture(
        self, remote_client, httpx_mock, basic_response_xml
    ):
        """Test the basic_response_xml fixture."""

        from urllib.parse import urlparse

        from hurl.schemas.requests import GetDataRequest
        from tests.conftest import remove_tags

        # Get the remote URL
        remote_url = GetDataRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            site="Manawatu at Teachers College",
            measurement="Stage",
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
        basic_response_xml_cleaned = remove_tags(basic_response_xml, ["T", "E"])

        # Compare the local and remote XML
        assert basic_response_xml_cleaned == remote_xml_cleaned

    @pytest.mark.remote
    @pytest.mark.update
    def test_one_point_response_xml_fixture(
        self, remote_client, httpx_mock, one_point_response_xml
    ):
        """Test the one_point_response_xml fixture."""

        from urllib.parse import urlparse

        from hurl.schemas.requests import GetDataRequest
        from tests.conftest import remove_tags

        # Get the remote URL
        remote_url = GetDataRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            site="Manawatu at Teachers College",
            measurement="Stage",
        ).gen_url()

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        # Get the remote XML
        remote_xml = remote_client.session.get(remote_url).text

        # remove the time tags (will change often)
        remote_xml_cleaned = remove_tags(remote_xml, ["T", "E"])
        one_point_response_xml_cleaned = remove_tags(one_point_response_xml, ["T", "E"])

        # Compare the local and remote XML
        assert one_point_response_xml_cleaned == remote_xml_cleaned

    @pytest.mark.remote
    @pytest.mark.update
    def test_collection_response_xml_fixture(
        self, remote_client, httpx_mock, collection_response_xml
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
            collection="Rainfall",
            from_datetime=start_timestamp,
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
            collection_response_xml, ["T", "E"]
        )

        # Compare the local and remote XML
        assert collection_response_xml_cleaned == remote_xml_cleaned

    @pytest.mark.remote
    @pytest.mark.update
    def test_time_interval_response_xml_fixture(
        self, remote_client, httpx_mock, time_interval_response_xml
    ):
        """Test the time_interval_response_xml fixture."""

        from urllib.parse import urlparse

        from hurl.schemas.requests import GetDataRequest

        # Get the remote URL
        remote_url = GetDataRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            site="Manawatu at Teachers College",
            measurement="Stage",
            time_interval="2023-01-01T12:00:00/2023-01-02T12:00:00",
        ).gen_url()

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        # Get the remote XML
        remote_xml = remote_client.session.get(remote_url).text

        # Compare the local and remote XML
        assert time_interval_response_xml == remote_xml

    @pytest.mark.remote
    @pytest.mark.update
    def test_time_interval_complex_response_xml_fixture(
        self, remote_client, httpx_mock, time_interval_complex_response_xml
    ):
        """Test the time_interval_response_xml fixture."""

        from urllib.parse import urlparse

        from hurl.schemas.requests import GetDataRequest

        # Get the remote URL
        remote_url = GetDataRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            site="Manawatu at Teachers College",
            measurement="Stage",
            time_interval="2023-01-01T12:00:00/P2DT2H",  # 2 days, 2 hours
            alignment="3h",  # Align to 3 hour intervals
        ).gen_url()

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        # Get the remote XML
        remote_xml = remote_client.session.get(remote_url).text

        # Compare the local and remote XML
        assert time_interval_complex_response_xml == remote_xml

    @pytest.mark.remote
    @pytest.mark.update
    def test_date_only_response_xml_fixture(
        self, remote_client, httpx_mock, date_only_response_xml
    ):
        """Test the time_interval_response_xml fixture."""

        from urllib.parse import urlparse

        from hurl.schemas.requests import GetDataRequest

        # Get the remote URL
        remote_url = GetDataRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            site="Manawatu at Teachers College",
            measurement="Stage",
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
        assert date_only_response_xml == remote_xml


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
            measurement="Test Measurement",
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
                measurement="Test Measurement",
                from_datetime="2023-01-01T00:00:00",
                to_datetime="2023-02-01T00:00:00",
            )

        assert isinstance(result, GetDataResponse)
        assert result.agency == "Test Council"

        # Check dataframe conversion
        df = result.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_basic_response_xml(self, httpx_mock, basic_response_xml):
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
            site="Manawatu at Teachers College",
            measurement="Stage",
            from_datetime="2023-01-01T00:00:00",
            to_datetime="2023-01-02T00:00:00",
        ).gen_url()

        # Here we tell httpx_mock to expect a GET request to the test_url, and
        # to return the basic_response_xml as the response.
        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=basic_response_xml,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:

            result = client.get_data(
                site="Manawatu at Teachers College",
                measurement="Stage",
                from_datetime="2023-01-01T00:00:00",
                to_datetime="2023-01-02T00:00:00",
            )

        # Base Model
        assert isinstance(result, GetDataResponse)
        assert result.agency == "Horizons"

        # Measurement
        assert len(result.measurement) == 1
        measurement = result.measurement[0]
        assert isinstance(measurement, GetDataResponse.Measurement)
        assert measurement.site_name == "Manawatu at Teachers College"

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

    def test_collection_response_xml(self, httpx_mock, collection_response_xml):
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
            text=collection_response_xml,
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
        assert result.agency == "Horizons"

        assert len(result.measurement) > 0
        assert isinstance(result.measurement, list)

        # Find the measurement with the site_name "Kahuterawa at Scotts Road"
        measurement = next(
            (
                m
                for m in result.measurement
                if m.site_name == "Kahuterawa at Scotts Road"
            ),
            None,
        )
        assert isinstance(measurement, GetDataResponse.Measurement)
        assert isinstance(
            measurement.data_source, GetDataResponse.Measurement.DataSource
        )

        # Test the data source
        data_source = measurement.data_source
        assert data_source.name == "SCADA Rainfall"
        assert data_source.num_items == 1
        assert data_source.ts_type == "StdSeries"
        assert data_source.data_type == "Rain6"
        assert data_source.interpolation == "Incremental"
        assert data_source.item_format is None
        assert len(data_source.item_info) == 1

        # Test the item info
        item_info = data_source.item_info[0]
        assert isinstance(item_info, GetDataResponse.Measurement.DataSource.ItemInfo)
        assert item_info.item_number == 1
        assert item_info.item_name == "Rainfall"
        assert item_info.item_format == "I"
        assert item_info.divisor is None
        assert item_info.units == "mm"
        assert item_info.format == "####.#"

        # Test the data
        data = measurement.data
        assert isinstance(data, GetDataResponse.Measurement.Data)
        assert data.date_format == "Calendar"
        assert data.num_items == 1
        assert isinstance(data.timeseries, pd.DataFrame)
        assert len(data.timeseries) > 0

        # Test the timeseries DataFrame
        assert data.timeseries.index.name == "DateTime"
        assert "Rainfall" in data.timeseries.columns
        assert data.timeseries.index.dtype == "datetime64[ns]"

    def test_one_point_response_xml(self, httpx_mock, one_point_response_xml):
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
            site="Manawatu at Teachers College",
            measurement="Stage",
        ).gen_url()

        # Here we tell httpx_mock to expect a GET request to the test_url, and
        # to return the one_point_response_xml as the response.
        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=one_point_response_xml,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:

            result = client.get_data(
                site="Manawatu at Teachers College",
                measurement="Stage",
            )

        # Test the top level response object
        assert isinstance(result, GetDataResponse)
        assert result.agency == "Horizons"

        assert len(result.measurement) > 0
        assert isinstance(result.measurement, list)

        # Find the measurement with the site_name "Manawatu at Teachers College"
        measurement = next(
            (
                m
                for m in result.measurement
                if m.site_name == "Manawatu at Teachers College"
            ),
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

    def test_time_interval_response_xml(self, httpx_mock, time_interval_response_xml):
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
            site="Manawatu at Teachers College",
            measurement="Stage",
            time_interval=time_interval,
        ).gen_url()

        # Here we tell httpx_mock to expect a GET request to the test_url, and
        # to return the one_point_response_xml as the response.
        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=time_interval_response_xml,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:

            result = client.get_data(
                site="Manawatu at Teachers College",
                measurement="Stage",
                time_interval=time_interval,
            )

        # Test the top level response object
        assert isinstance(result, GetDataResponse)
        assert result.agency == "Horizons"

        assert len(result.measurement) > 0
        assert isinstance(result.measurement, list)

        # Find the measurement with the site_name "Manawatu at Teachers College"
        measurement = next(
            (
                m
                for m in result.measurement
                if m.site_name == "Manawatu at Teachers College"
            ),
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

    def test_time_interval_complex_response_xml(
        self, httpx_mock, time_interval_complex_response_xml
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
            site="Manawatu at Teachers College",
            measurement="Stage",
            time_interval=time_interval,
            alignment=alignment,
        ).gen_url()

        # Here we tell httpx_mock to expect a GET request to the test_url, and
        # to return the one_point_response_xml as the response.
        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=time_interval_complex_response_xml,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:

            result = client.get_data(
                site="Manawatu at Teachers College",
                measurement="Stage",
                time_interval=time_interval,
                alignment=alignment,
            )

        # Test the top level response object
        assert isinstance(result, GetDataResponse)
        assert result.agency == "Horizons"

        assert len(result.measurement) > 0
        assert isinstance(result.measurement, list)

        # Find the measurement with the site_name "Manawatu at Teachers College"
        measurement = next(
            (
                m
                for m in result.measurement
                if m.site_name == "Manawatu at Teachers College"
            ),
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
