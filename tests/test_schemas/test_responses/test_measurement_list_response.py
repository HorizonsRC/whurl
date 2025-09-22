"""Test the MeasurementListReponse class."""

import os

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

        from whurl.schemas.requests import MeasurementListRequest

        path = (
            Path(__file__).parent.parent.parent
            / "fixture_cache"
            / "measurement_list"
            / filename
        )
        if request.config.getoption("--update"):
            # Switch off httpx mock so that cached request can go through.
            httpx_mock._options.should_mock = (
                lambda request: request.url.host
                != urlparse(remote_client.base_url).netloc
            )
            cached_url = MeasurementListRequest(
                base_url=remote_client.base_url,
                hts_endpoint=remote_client.hts_endpoint,
                **(request_kwargs or {}),
            ).gen_url()
            cached_xml = remote_client.session.get(cached_url).text
            path.write_text(cached_xml, encoding="utf-8")
        
        # Skip gracefully if fixture cache file doesn't exist in offline mode
        if not path.exists():
            pytest.skip(f"Fixture cache file not found: {path.name}. Use --update flag to populate from remote API.")
        
        raw_xml = path.read_text(encoding="utf-8")
        return raw_xml

    return fixture_func


# Create cached fixtures
multi_response_xml_cached = create_cached_fixtures(
    "multi_response.xml", {"site": os.getenv("TEST_SITE")}
)
all_response_xml_cached = create_cached_fixtures("all_response.xml")
error_response_xml_cached = create_cached_fixtures(
    "error_response.xml", {"site": "NotARealSite"}
)
units_response_xml_cached = create_cached_fixtures(
    "units_response.xml", {"units": "Yes"}
)


def create_mocked_fixtures(filename: str):
    """Factory to create mocked fixtures."""

    @pytest.fixture
    def fixture_func():
        """Load test XML once per test session."""
        from pathlib import Path

        path = (
            Path(__file__).parent.parent.parent
            / "mocked_data"
            / "measurement_list"
            / filename
        )
        raw_xml = path.read_text(encoding="utf-8")
        return raw_xml

    return fixture_func


multi_response_xml_mocked = create_mocked_fixtures("multi_response.xml")
all_response_xml_mocked = create_mocked_fixtures("all_response.xml")
error_response_xml_mocked = create_mocked_fixtures("error_response.xml")
units_response_xml_mocked = create_mocked_fixtures("units_response.xml")


class VerifyCachedFixtures:
    @pytest.mark.remote
    @pytest.mark.integration
    def test_multi_response_xml_cache(
        self,
        remote_client,
        httpx_mock,
        multi_response_xml_cached,
    ):
        """Validate the XML response from Hilltop Server."""
        from urllib.parse import urlparse

        from whurl.schemas.requests import MeasurementListRequest
        from tests.conftest import remove_tags

        # Generate the remote URL
        remote_url = MeasurementListRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            site=os.getenv("TEST_SITE"),
        ).gen_url()

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        remote_xml = remote_client.session.get(remote_url).text

        tags_to_remove = [
            "To",
            "VMFinish",
        ]

        # remove the tags To, VMFinish
        remote_xml_cleaned = remove_tags(remote_xml, tags_to_remove)
        multi_response_xml_cleaned = remove_tags(
            multi_response_xml_cached, tags_to_remove
        )

        assert remote_xml_cleaned == multi_response_xml_cleaned

    @pytest.mark.remote
    @pytest.mark.integration
    def test_all_response_xml_fixture(
        self,
        remote_client,
        httpx_mock,
        all_response_xml_cached,
    ):
        """Validate the XML response from Hilltop Server."""
        from urllib.parse import urlparse

        from whurl.schemas.requests import MeasurementListRequest

        cached_xml = all_response_xml_cached

        remote_url = MeasurementListRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
        ).gen_url()

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        remote_xml = remote_client.session.get(remote_url).text

        assert remote_xml == cached_xml

    @pytest.mark.remote
    @pytest.mark.integration
    def test_error_response_xml_fixture(
        self,
        remote_client,
        httpx_mock,
        error_response_xml_cached,
    ):
        """Validate the XML Error response from Hilltop Server."""
        from urllib.parse import urlparse

        from whurl.schemas.requests import MeasurementListRequest

        cached_xml = error_response_xml_cached

        remote_url = MeasurementListRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            site="NotARealSite",
        ).gen_url()

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        remote_xml = remote_client.session.get(remote_url).text

        assert remote_xml == cached_xml

    @pytest.mark.remote
    @pytest.mark.integration
    def test_units_response_xml_fixture(
        self,
        remote_client,
        httpx_mock,
        units_response_xml_cached,
    ):
        """Validate the XML units response from Hilltop Server."""
        from urllib.parse import urlparse

        from whurl.schemas.requests import MeasurementListRequest

        cached_xml = units_response_xml_cached

        remote_url = MeasurementListRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            units="Yes",
        ).gen_url()

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        remote_xml = remote_client.session.get(remote_url).text

        assert remote_xml == cached_xml


class TestMeasurementList:
    @pytest.mark.unit
    def test_all_response_xml_unit(self, httpx_mock, all_response_xml_mocked):
        """Test that the XML can be parsed into a MeasurementListResponse object."""

        from whurl.client import HilltopClient
        from whurl.schemas.requests import MeasurementListRequest
        from whurl.schemas.responses import MeasurementListResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        # Generate the remote URL
        test_url = MeasurementListRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=all_response_xml_mocked,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            measurement_list = client.get_measurement_list()

        # Test the top level response object
        assert isinstance(measurement_list, MeasurementListResponse)
        assert measurement_list.agency == "Test Council"

        assert len(measurement_list.measurements) > 0

        sg_measurement = next(
            (m for m in measurement_list.measurements if m.name == "Flow"),
            None,
        )
        print(measurement_list.measurements)

        assert sg_measurement is not None
        assert sg_measurement.name == "Flow"

    @pytest.mark.integration
    def test_all_response_xml_integration(self, httpx_mock, all_response_xml_cached):
        """Test that the XML can be parsed into a MeasurementListResponse object."""

        from whurl.client import HilltopClient
        from whurl.schemas.requests import MeasurementListRequest
        from whurl.schemas.responses import MeasurementListResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        # Generate the remote URL
        test_url = MeasurementListRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=all_response_xml_cached,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            measurement_list = client.get_measurement_list()

        # Test the top level response object
        assert isinstance(measurement_list, MeasurementListResponse)
        assert measurement_list.agency == os.getenv("TEST_AGENCY")

        assert len(measurement_list.measurements) > 0

        sg_measurement = next(
            (
                m
                for m in measurement_list.measurements
                if m.name == os.getenv("TEST_MEASUREMENT")
            ),
            None,
        )
        print(measurement_list.measurements)

        assert sg_measurement is not None
        assert sg_measurement.name == os.getenv("TEST_MEASUREMENT")

    @pytest.mark.unit
    def test_error_from_xml_unit(self, httpx_mock, error_response_xml_mocked):
        """Test that the XML can be parsed into a MeasurementListResponse object."""

        from whurl.client import HilltopClient
        from whurl.exceptions import HilltopResponseError
        from whurl.schemas.requests import MeasurementListRequest
        from whurl.schemas.responses import MeasurementListResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        # Generate the remote URL
        test_url = MeasurementListRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=error_response_xml_mocked,
        )

        with pytest.raises(HilltopResponseError):
            with HilltopClient(
                base_url=base_url,
                hts_endpoint=hts_endpoint,
            ) as client:
                measurement_list = client.get_measurement_list()

    @pytest.mark.integration
    def test_error_from_xml_integration(self, httpx_mock, error_response_xml_cached):
        """Test that the XML can be parsed into a MeasurementListResponse object."""

        from whurl.client import HilltopClient
        from whurl.exceptions import HilltopResponseError
        from whurl.schemas.requests import MeasurementListRequest
        from whurl.schemas.responses import MeasurementListResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        # Generate the remote URL
        test_url = MeasurementListRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=error_response_xml_cached,
        )

        with pytest.raises(HilltopResponseError):
            with HilltopClient(
                base_url=base_url,
                hts_endpoint=hts_endpoint,
            ) as client:
                measurement_list = client.get_measurement_list()

    @pytest.mark.unit
    def test_multi_response_xml_unit(self, httpx_mock, multi_response_xml_mocked):
        """Test multiple measurement response."""
        import pandas as pd

        from whurl.client import HilltopClient
        from whurl.schemas.requests import MeasurementListRequest
        from whurl.schemas.responses import MeasurementListResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        # Generate the remote URL
        test_url = MeasurementListRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site="Test Site 123",
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=multi_response_xml_mocked,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            measurement_list = client.get_measurement_list(
                site="Test Site 123",
            )

        # Test the top level response object
        assert isinstance(measurement_list, MeasurementListResponse)
        assert measurement_list.agency == "Test Council"

        # Test a specific data source
        flow_ds = next(
            (ds for ds in measurement_list.data_sources if ds.name == "Flow"),
            None,
        )
        assert isinstance(flow_ds, MeasurementListResponse.DataSource)
        assert flow_ds.site == "Test Site 123"
        assert len(flow_ds.measurements) > 0

        # Test a specific measurement
        stage_measurement = next(
            (
                m
                for m in flow_ds.measurements
                if m.name == "Stage"
            ),
            None,
        )
        assert isinstance(
            stage_measurement, MeasurementListResponse.DataSource.Measurement
        )
        flow_dev_measurement = next(
            (
                m
                for m in flow_ds.measurements
                if m.name == "Monthly Flow Deviation (monthly median)"
            ),
            None,
        )
        assert isinstance(
            flow_dev_measurement, MeasurementListResponse.DataSource.Measurement
        )

        assert stage_measurement.units == "mm"
        assert stage_measurement.default_measurement is True
        assert flow_dev_measurement.default_measurement is False

        ml_df = measurement_list.to_dataframe()

        assert len(ml_df) > 0
        assert isinstance(ml_df, pd.DataFrame)

    @pytest.mark.integration
    def test_multi_response_xml_integration(
        self, httpx_mock, multi_response_xml_cached
    ):
        """Test multiple measurement response."""
        import pandas as pd

        from whurl.client import HilltopClient
        from whurl.schemas.requests import MeasurementListRequest
        from whurl.schemas.responses import MeasurementListResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        # Generate the remote URL
        test_url = MeasurementListRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site=os.getenv("TEST_SITE"),
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=multi_response_xml_cached,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            measurement_list = client.get_measurement_list(
                site=os.getenv("TEST_SITE"),
            )

        # Test the top level response object
        assert isinstance(measurement_list, MeasurementListResponse)
        assert measurement_list.agency == os.getenv("TEST_AGENCY")

        # Test a specific data source
        test_ds = next(
            (
                ds
                for ds in measurement_list.data_sources
                if ds.name == os.getenv("TEST_DATA_SOURCE")
            ),
            None,
        )
        assert isinstance(test_ds, MeasurementListResponse.DataSource)
        assert test_ds.site == os.getenv("TEST_SITE")
        assert len(test_ds.measurements) > 0

        # Test a specific measurement
        test_measurement = next(
            (
                m
                for m in test_ds.measurements
                if m.name == os.getenv("TEST_MEASUREMENT")
            ),
            None,
        )
        assert isinstance(
            test_measurement, MeasurementListResponse.DataSource.Measurement
        )

        df = measurement_list.to_dataframe()

        assert len(df) > 0
        assert isinstance(df, pd.DataFrame)

    @pytest.mark.unit
    def test_units_response_xml_unit(self, httpx_mock, units_response_xml_mocked):
        """Test that the XML can be parsed into a MeasurementListResponse object."""
        from whurl.client import HilltopClient
        from whurl.schemas.requests import MeasurementListRequest
        from whurl.schemas.responses import MeasurementListResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        # Generate the remote URL
        test_url = MeasurementListRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site="Test Site 123",
            units="Yes",
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=units_response_xml_mocked,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            measurement_list = client.get_measurement_list(
                site="Test Site 123",
                units="Yes",
            )

        # Test the top level response object
        assert isinstance(measurement_list, MeasurementListResponse)
        assert measurement_list.agency == "Test Council"
        assert len(measurement_list.measurements) > 0
        sg_measurement = next(
            (m for m in measurement_list.measurements if m.name == "Flow"),
            None,
        )
        assert sg_measurement is not None
        assert sg_measurement.name == "Flow"
        assert sg_measurement.units == "m3/s"

    @pytest.mark.integration
    def test_units_response_xml_integration(
        self, httpx_mock, units_response_xml_cached
    ):
        """Test that the XML can be parsed into a MeasurementListResponse object."""
        from whurl.client import HilltopClient
        from whurl.schemas.requests import MeasurementListRequest
        from whurl.schemas.responses import MeasurementListResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        # Generate the remote URL
        test_url = MeasurementListRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site=os.getenv("TEST SITE"),
            units="Yes",
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=units_response_xml_cached,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            measurement_list = client.get_measurement_list(
                site=os.getenv("TEST SITE"),
                units="Yes",
            )

        # Test the top level response object
        assert isinstance(measurement_list, MeasurementListResponse)
        assert measurement_list.agency == os.getenv("TEST_AGENCY")
        assert len(measurement_list.measurements) > 0
        sg_measurement = next(
            (m for m in measurement_list.measurements if m.name == "Flow"),
            None,
        )
        assert sg_measurement is not None
        assert sg_measurement.name == "Flow"
        assert sg_measurement.units == "l/s"

    @pytest.mark.unit
    def test_to_dict_unit(self, all_response_xml_mocked):
        """Test to_dict method."""
        import xmltodict

        from whurl.schemas.responses import MeasurementListResponse

        site_list = MeasurementListResponse.from_xml(str(all_response_xml_mocked))
        # Convert to dictionary
        test_dict = site_list.to_dict()

        test_dict = {
            k: (
                str(v)
                if not isinstance(v, list) and v is not None
                else (
                    [
                        {
                            kk: str(vv) if str(vv) != "None" else None
                            for kk, vv in i.items()
                        }
                        for i in v
                    ]
                    if isinstance(v, list)
                    else v
                )
            )
            for k, v in test_dict.items()
        }

        naive_dict = xmltodict.parse(all_response_xml_mocked)["HilltopServer"]

        assert test_dict == naive_dict

    @pytest.mark.integration
    def test_to_dict_integration(self, all_response_xml_cached):
        """Test to_dict method."""
        import xmltodict

        from whurl.schemas.responses import MeasurementListResponse

        site_list = MeasurementListResponse.from_xml(str(all_response_xml_cached))
        # Convert to dictionary
        test_dict = site_list.to_dict()

        test_dict = {
            k: (
                str(v)
                if not isinstance(v, list) and v is not None
                else (
                    [
                        {
                            kk: str(vv) if str(vv) != "None" else None
                            for kk, vv in i.items()
                        }
                        for i in v
                    ]
                    if isinstance(v, list)
                    else v
                )
            )
            for k, v in test_dict.items()
        }

        naive_dict = xmltodict.parse(all_response_xml_cached)["HilltopServer"]

        assert test_dict == naive_dict
