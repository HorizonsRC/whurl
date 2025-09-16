"""Test the MeasurementListReponse class."""

import pytest


def create_measurement_list_fixture(filename: str, request_kwargs: dict = None):
    """Factory to create measurement list fixtures with data source support."""
    
    @pytest.fixture
    def fixture_func(request, httpx_mock, remote_client):
        """Load measurement list XML with multiple data source support."""
        from pathlib import Path
        from urllib.parse import urlparse
        
        from hurl.schemas.requests import MeasurementListRequest
        from tests.test_data_sources import TestDataManager, TestDataSource

        # Initialize data manager
        manager = TestDataManager(Path(__file__))
        data_type = "measurement_list"

        # Handle remote updates (--update flag)
        if request.config.getoption("--update"):
            # Switch off httpx mock so that remote request can go through
            httpx_mock._options.should_mock = (
                lambda request: request.url.host != urlparse(remote_client.base_url).netloc
            )

            remote_url = MeasurementListRequest(
                base_url=remote_client.base_url,
                hts_endpoint=remote_client.hts_endpoint,
                **(request_kwargs or {})
            ).gen_url()
            remote_xml = remote_client.session.get(remote_url).text
            
            # Save to cache
            cache_path = manager.cached_dir / data_type / filename
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(remote_xml, encoding="utf-8")
            
            return remote_xml

        # Get preferred data source from CLI option
        data_source_option = request.config.getoption("--data-source")
        preferred_source = None
        if data_source_option != "auto":
            preferred_source = TestDataSource(data_source_option)

        # Get data file with fallback logic
        data_file = manager.get_data_file(data_type, filename, preferred_source)
        
        if data_file is None:
            available_sources = manager.get_available_sources(data_type, filename)
            pytest.skip(
                f"No data available for {data_type}/{filename}. "
                f"Available sources: {[s.value for s in available_sources]}. "
                f"Use --data-source to specify preference or --update to fetch remote data."
            )

        return data_file.read_text(encoding="utf-8")
    
    return fixture_func


# Create fixtures for different measurement list scenarios
multi_response_xml = create_measurement_list_fixture(
    "multi_response.xml", 
    {"site": "Test Site Alpha"}
)

all_response_xml = create_measurement_list_fixture(
    "all_response.xml"
)

error_response_xml = create_measurement_list_fixture(
    "error_response.xml",
    {"site": "Invalid Site Name"}
)

units_response_xml = create_measurement_list_fixture(
    "units_response.xml",
    {"units": "Yes"}
)


class TestRemoteFixtures:
    """Test fixture validation against remote API (integration testing)."""
    
    @pytest.mark.remote
    @pytest.mark.update
    @pytest.mark.integration
    @pytest.mark.remote_data
    def test_multi_response_xml_fixture(
        self,
        remote_client,
        httpx_mock,
        multi_response_xml,
    ):
        """Validate the XML response from Hilltop Server."""
        from urllib.parse import urlparse

        from hurl.schemas.requests import MeasurementListRequest
        from tests.conftest import remove_tags

        # Generate the remote URL
        remote_url = MeasurementListRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            site="Manawatu at Teachers College",
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
        multi_response_xml_cleaned = remove_tags(multi_response_xml, tags_to_remove)

        assert remote_xml_cleaned == multi_response_xml_cleaned

    @pytest.mark.remote
    @pytest.mark.update
    @pytest.mark.integration
    @pytest.mark.remote_data
    def test_all_response_xml_fixture(
        self,
        remote_client,
        httpx_mock,
        all_response_xml,
    ):
        """Validate the XML response from Hilltop Server."""
        from urllib.parse import urlparse

        from hurl.schemas.requests import MeasurementListRequest

        cached_xml = all_response_xml

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
    @pytest.mark.update
    @pytest.mark.integration
    @pytest.mark.remote_data
    def test_error_response_xml_fixture(
        self,
        remote_client,
        httpx_mock,
        error_response_xml,
    ):
        """Validate the XML Error response from Hilltop Server."""
        from urllib.parse import urlparse

        from hurl.schemas.requests import MeasurementListRequest

        cached_xml = error_response_xml

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
    @pytest.mark.update
    def test_units_response_xml_fixture(
        self,
        remote_client,
        httpx_mock,
        units_response_xml,
    ):
        """Validate the XML units response from Hilltop Server."""
        from urllib.parse import urlparse

        from hurl.schemas.requests import MeasurementListRequest

        cached_xml = units_response_xml

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
    """Unit tests for measurement list response schema validation (CI-safe)."""

    @pytest.mark.unit
    @pytest.mark.mocked_data
    def test_all_reponse_xml(self, httpx_mock, all_response_xml):
        """Test that the XML can be parsed into a MeasurementListResponse object."""

        from hurl.client import HilltopClient
        from hurl.schemas.requests import MeasurementListRequest
        from hurl.schemas.responses import MeasurementListResponse

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
            text=all_response_xml,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            measurement_list = client.get_measurement_list()

        # Test the top level response object
        assert isinstance(measurement_list, MeasurementListResponse)
        # Unit tests should check specific mocked data values  
        assert measurement_list.agency == "Test Council"

        # Check both top-level measurements and data source measurements
        all_measurements = measurement_list.measurements
        if len(measurement_list.data_sources) > 0:
            for ds in measurement_list.data_sources:
                all_measurements.extend(ds.measurements)

        assert len(all_measurements) > 0

        # Look for any measurement that exists in our mocked data
        flow_measurement = next(
            (
                m
                for m in all_measurements
                if "Flow" in m.name
            ),
            None,
        )

        assert flow_measurement is not None
        # Just verify that a flow measurement exists, flexible for both real and mocked data
        assert "Flow" in flow_measurement.name

    @pytest.mark.unit
    @pytest.mark.mocked_data
    def test_error_from_xml(self, httpx_mock, error_response_xml):
        """Test that the XML can be parsed into a MeasurementListResponse object."""

        from hurl.client import HilltopClient
        from hurl.exceptions import HilltopResponseError
        from hurl.schemas.requests import MeasurementListRequest
        from hurl.schemas.responses import MeasurementListResponse

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
            text=error_response_xml,
        )

        with pytest.raises(HilltopResponseError):
            with HilltopClient(
                base_url=base_url,
                hts_endpoint=hts_endpoint,
            ) as client:
                measurement_list = client.get_measurement_list()

    @pytest.mark.unit
    @pytest.mark.mocked_data  
    def test_multi_response_xml(self, httpx_mock, multi_response_xml):
        """Test multiple measurement response."""
        import pandas as pd

        from hurl.client import HilltopClient
        from hurl.schemas.requests import MeasurementListRequest
        from hurl.schemas.responses import MeasurementListResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        # Generate the remote URL
        test_url = MeasurementListRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site="Manawatu at Teachers College",
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=multi_response_xml,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            measurement_list = client.get_measurement_list(
                site="Manawatu at Teachers College",
            )

        # Test the top level response object
        assert isinstance(measurement_list, MeasurementListResponse)
        # Unit tests should check specific mocked data values
        assert measurement_list.agency == "Test Council"

        # Test a specific data source
        water_level_ds = next(
            (ds for ds in measurement_list.data_sources if ds.name == "Water Level"),
            None,
        )
        assert isinstance(water_level_ds, MeasurementListResponse.DataSource)
        assert water_level_ds.site == "Manawatu at Teachers College"
        assert len(water_level_ds.measurements) > 0

        # Test a specific measurement
        stage_measurement = next(
            (m for m in water_level_ds.measurements if m.name == "Stage"), None
        )
        assert isinstance(
            stage_measurement, MeasurementListResponse.DataSource.Measurement
        )
        mean_v_measurement = next(
            (m for m in water_level_ds.measurements if m.name == "Mean Velocity"), None
        )
        assert isinstance(
            mean_v_measurement, MeasurementListResponse.DataSource.Measurement
        )

        assert stage_measurement.units == "mm"
        assert stage_measurement.default_measurement is True
        assert mean_v_measurement.default_measurement is False

        ml_df = measurement_list.to_dataframe()

        assert len(ml_df) > 0
        assert isinstance(ml_df, pd.DataFrame)

    @pytest.mark.unit
    @pytest.mark.mocked_data
    def test_units_response_xml(self, httpx_mock, units_response_xml):
        """Test that the XML can be parsed into a MeasurementListResponse object."""
        from hurl.client import HilltopClient
        from hurl.schemas.requests import MeasurementListRequest
        from hurl.schemas.responses import MeasurementListResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        # Generate the remote URL
        test_url = MeasurementListRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site="Manawatu at Teachers College",
            units="Yes",
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=units_response_xml,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            measurement_list = client.get_measurement_list(
                site="Manawatu at Teachers College",
                units="Yes",
            )

        # Test the top level response object
        assert isinstance(measurement_list, MeasurementListResponse)
        # Unit tests should check specific mocked data values
        assert measurement_list.agency == "Test Council"
        assert len(measurement_list.measurements) > 0
        sg_measurement = next(
            (m for m in measurement_list.measurements if m.name == "Groundwater"),
            None,
        )
        assert sg_measurement is not None
        assert sg_measurement.name == "Groundwater"
        assert sg_measurement.units == "mm"

    @pytest.mark.unit
    @pytest.mark.mocked_data
    def test_to_dict(self, all_response_xml):
        """Test to_dict method."""
        import xmltodict

        from hurl.schemas.responses import MeasurementListResponse

        site_list = MeasurementListResponse.from_xml(str(all_response_xml))
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

        naive_dict = xmltodict.parse(all_response_xml)["HilltopServer"]

        assert test_dict == naive_dict
