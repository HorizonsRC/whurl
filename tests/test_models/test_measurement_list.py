from pathlib import Path

import pandas as pd
import pytest

from hurl.client import HilltopClient
from hurl.exceptions import HilltopResponseError
from hurl.models.measurement_list import HilltopMeasurementList
from tests.conftest import remove_tags


@pytest.fixture
def multi_response_xml(request, remote_client):
    """Load test XML once per test session."""
    path = (
        Path(__file__).parent.parent
        / "fixture_cache"
        / "measurement_list"
        / "multi_response.xml"
    )

    if request.config.getoption("--update"):
        remote_url = HilltopMeasurementList.gen_url(
            remote_client.base_url,
            remote_client.hts_endpoint,
            site="Manawatu at Teachers College",
        )
        remote_xml = remote_client.session.get(remote_url).text

        path.write_text(remote_xml, encoding="utf-8")

    raw_xml = path.read_text(encoding="utf-8")

    return raw_xml


@pytest.fixture
def all_response_xml(request, remote_client):
    """Load test XML once per test session."""
    path = (
        Path(__file__).parent.parent
        / "fixture_cache"
        / "measurement_list"
        / "all_response.xml"
    )

    if request.config.getoption("--update"):
        remote_url = HilltopMeasurementList.gen_url(
            remote_client.base_url,
            remote_client.hts_endpoint,
        )
        remote_xml = remote_client.session.get(remote_url).text

        path.write_text(remote_xml, encoding="utf-8")

    raw_xml = path.read_text(encoding="utf-8")

    return raw_xml


@pytest.fixture
def error_response_xml(request, remote_client):
    """Load test XML once per test session."""
    path = (
        Path(__file__).parent.parent
        / "fixture_cache"
        / "measurement_list"
        / "error_response.xml"
    )

    if request.config.getoption("--update"):
        remote_url = HilltopMeasurementList.gen_url(
            remote_client.base_url,
            remote_client.hts_endpoint,
            site="Not a real site",
        )
        remote_xml = remote_client.session.get(remote_url).text

        path.write_text(remote_xml, encoding="utf-8")

    raw_xml = path.read_text(encoding="utf-8")

    return raw_xml


@pytest.fixture
def mock_hilltop_client(mocker, multi_response_xml):
    """Mock HilltopClient."""
    # Mock the response
    mock_response = mocker.MagicMock()
    mock_response.text = multi_response_xml
    mock_response.status_code = 200

    # Mock the session
    mock_session = mocker.MagicMock()
    mock_session.get.return_value = mock_response

    # Mock the client context manager
    mock_client = mocker.MagicMock()
    mock_client.base_url = "http://example.com"
    mock_client.hts_endpoint = "foo.hts"
    mock_client.timeout = 60
    mock_client.__enter__.return_value = mock_client  # Returns self
    mock_client.__exit__.return_value = None
    mock_client.session = mock_session

    # Patch the real client
    mocker.patch("hurl.client.HilltopClient", return_value=mock_client)

    return {
        "client": mock_client,
        "session": mock_session,
        "response": mock_response,
    }


class TestRemoteFixtures:
    @pytest.mark.remote
    @pytest.mark.update
    def test_multi_response_xml_fixture(
        self,
        remote_client,
        multi_response_xml,
    ):
        """Validate the XML response from Hilltop Server."""
        from hurl.models.measurement_list import HilltopMeasurementList

        cached_xml = multi_response_xml

        remote_url = HilltopMeasurementList.gen_url(
            remote_client.base_url,
            remote_client.hts_endpoint,
            site="Manawatu at Teachers College",
        )
        remote_xml = remote_client.session.get(remote_url).text

        tags_to_remove = [
            "To",
            "VMFinish",
        ]

        # remove the tags To, VMFinish
        remote_xml_cleaned = remove_tags(
            remote_xml, tags_to_remove
        )
        cached_xml_cleaned = remove_tags(
            cached_xml, tags_to_remove
        )

        assert remote_xml_cleaned == cached_xml_cleaned

    @pytest.mark.remote
    @pytest.mark.update
    def test_all_response_xml_fixture(
        self,
        remote_client,
        all_response_xml,
    ):
        """Validate the XML response from Hilltop Server."""
        from hurl.models.measurement_list import HilltopMeasurementList

        cached_xml = all_response_xml

        remote_url = HilltopMeasurementList.gen_url(
            remote_client.base_url,
            remote_client.hts_endpoint,
        )
        print(remote_url)
        remote_xml = remote_client.session.get(remote_url).text

        assert remote_xml == cached_xml

    @pytest.mark.remote
    @pytest.mark.update
    def test_error_response_xml_fixture(
        self,
        remote_client,
        error_response_xml,
    ):
        """Validate the XML Error response from Hilltop Server."""
        from hurl.models.measurement_list import HilltopMeasurementList

        cached_xml = error_response_xml

        remote_url = HilltopMeasurementList.gen_url(
            remote_client.base_url,
            remote_client.hts_endpoint,
            site="NotARealSite",
        )
        remote_xml = remote_client.session.get(remote_url).text

        assert remote_xml == cached_xml


class TestMeasurementList:
    def test_gen_measurement_list_url(self):
        from hurl.models.measurement_list import (HilltopMeasurementList,
                                                  gen_measurement_list_url)

        correct_url = (
            "http://example.com/foo.hts?"
            "Request=MeasurementList"
            "&Service=Hilltop"
            "&Site=River%20At%20Site"
            "&Collection=collection"
            "&Units=units"
            "&Target=target"
        )

        test_url = gen_measurement_list_url(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            site="River At Site",
            collection="collection",
            units="units",
            target="target",
        )
        assert test_url == correct_url

        blank_url = gen_measurement_list_url(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
        )
        assert blank_url == (
            "http://example.com/foo.hts?Request=MeasurementList&Service=Hilltop"
        )

        test_method_gen_url = HilltopMeasurementList.gen_url(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            site="River At Site",
            collection="collection",
            units="units",
            target="target",
        )

        assert test_method_gen_url == correct_url

    def test_from_url(self, mock_hilltop_client):
        """Test from_url method."""
        mock_client = mock_hilltop_client["client"]
        mock_session = mock_hilltop_client["session"]

        test_url = (
            "http://example.com/foo.hts?"
            "Request=MeasurementList"
            "&Service=Hilltop"
            "&Site=Manawatu%20At%20Teachers%20College"
        )

        # 5. Test the actual method
        measurement_list = HilltopMeasurementList.from_url(
            test_url, timeout=60, client=mock_client
        )

        # 6. Verify behavior
        mock_session.get.assert_called_once_with(test_url, timeout=60)

        # Test the top level response object
        assert isinstance(measurement_list, HilltopMeasurementList)
        assert measurement_list.agency == "Horizons"

        # Test a specific data source
        water_level_ds = next(
            (ds for ds in measurement_list.data_sources if ds.name == "Water Level"),
            None,
        )
        assert water_level_ds.site == "Manawatu at Teachers College"
        assert len(water_level_ds.measurements) > 0

        # Test a specific measurement
        stage_measurement = next(
            (m for m in water_level_ds.measurements if m.name == "Stage"), None
        )
        mean_v_measurement = next(
            (m for m in water_level_ds.measurements if m.name == "Mean Velocity"), None
        )

        assert stage_measurement.units == "mm"
        assert stage_measurement.default_measurement is True
        assert mean_v_measurement.default_measurement is False

        ml_df = measurement_list.to_dataframe()

        assert len(ml_df) > 0
        assert isinstance(ml_df, pd.DataFrame)

    def test_from_params(self, mock_hilltop_client):
        """Test from_params method."""
        mock_client = mock_hilltop_client["client"]
        mock_session = mock_hilltop_client["session"]

        measurement_list = HilltopMeasurementList.from_params(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            site="Manawatu At Teachers College",
            collection="collection",
            units="units",
            target="target",
            timeout=60,
            client=mock_client,
        )

        test_url = (
            "http://example.com/foo.hts?"
            "Request=MeasurementList"
            "&Service=Hilltop"
            "&Site=Manawatu%20At%20Teachers%20College"
            "&Collection=collection"
            "&Units=units"
            "&Target=target"
        )

        mock_session.get.assert_called_once_with(
            test_url,
            timeout=60,
        )

        # Test the top level response object
        assert isinstance(measurement_list, HilltopMeasurementList)
        assert measurement_list.agency == "Horizons"

        # Test a specific data source
        water_level_ds = next(
            (ds for ds in measurement_list.data_sources if ds.name == "Water Level"),
            None,
        )
        assert water_level_ds.site == "Manawatu at Teachers College"
        assert len(water_level_ds.measurements) > 0

        # Test a specific measurement
        stage_measurement = next(
            (m for m in water_level_ds.measurements if m.name == "Stage"), None
        )
        mean_v_measurement = next(
            (m for m in water_level_ds.measurements if m.name == "Mean Velocity"), None
        )

        assert stage_measurement.units == "mm"
        assert stage_measurement.default_measurement is True
        assert mean_v_measurement.default_measurement is False

        ml_df = measurement_list.to_dataframe()

        assert len(ml_df) > 0
        assert isinstance(ml_df, pd.DataFrame)

    def test_multi_response_from_xml(
        self,
        multi_response_xml,
    ):
        """Test that the XML can be parsed into a HilltopMeasurementList object."""
        cached_xml = multi_response_xml

        # Parse the XML into a HilltopMeasurementList object
        measurement_list = HilltopMeasurementList.from_xml(cached_xml)

        # Test the top level response object
        assert isinstance(measurement_list, HilltopMeasurementList)
        assert measurement_list.agency == "Horizons"

        # Test a specific data source
        water_level_ds = next(
            (ds for ds in measurement_list.data_sources if ds.name == "Water Level"),
            None,
        )
        assert water_level_ds.site == "Manawatu at Teachers College"
        assert len(water_level_ds.measurements) > 0

        # Test a specific measurement
        stage_measurement = next(
            (m for m in water_level_ds.measurements if m.name == "Stage"), None
        )
        mean_v_measurement = next(
            (m for m in water_level_ds.measurements if m.name == "Mean Velocity"), None
        )

        assert stage_measurement.units == "mm"
        assert stage_measurement.default_measurement is True
        assert mean_v_measurement.default_measurement is False

        ml_df = measurement_list.to_dataframe()
        assert len(ml_df) > 0
        assert isinstance(ml_df, pd.DataFrame)

    def test_all_from_xml(self, all_response_xml):
        """Test that the XML can be parsed into a HilltopMeasurementList object."""
        cached_xml = all_response_xml

        # Parse the XML into a HilltopMeasurementList object
        measurement_list = HilltopMeasurementList.from_xml(cached_xml)

        # Test the top level response object
        assert isinstance(measurement_list, HilltopMeasurementList)
        assert measurement_list.agency == "Horizons"

        assert len(measurement_list.measurements) > 0

        sg_measurement = next(
            (
                m
                for m in measurement_list.measurements
                if m.name == "Internal S.G. [Water Level]"
            ),
            None,
        )

        assert sg_measurement is not None
        assert sg_measurement.name == "Internal S.G. [Water Level]"

    @pytest.mark.xfail(
        reason="Validator expected to fail upon encoutering a hilltop error response.",
        raises=HilltopResponseError,
    )
    def test_error_from_xml(self, error_response_xml):
        """Test that the XML can be parsed into a HilltopMeasurementList object."""
        cached_xml = error_response_xml

        # Parse the XML into a HilltopMeasurementList object
        measurement_list = HilltopMeasurementList.from_xml(cached_xml)

    def test_to_dict(self, all_response_xml):
        """Test to_dict method."""
        import xmltodict

        site_list = HilltopMeasurementList.from_xml(all_response_xml)
        # Convert to dictionary
        test_dict = site_list.to_dict()

        test_dict = {
            k: (
                str(v)
                if not isinstance(v, list) and v is not None
                else [
                    {
                        kk: str(vv) if str(vv) != 'None' else None
                        for kk, vv in i.items()
                    }
                    for i in v
                ] if isinstance(v, list) else v
            )
            for k, v in test_dict.items()
        }

        naive_dict = xmltodict.parse(all_response_xml)["HilltopServer"]

        assert test_dict == naive_dict
