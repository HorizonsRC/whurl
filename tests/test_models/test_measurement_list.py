"""Test the HilltopMeasurementList class."""

import pytest


@pytest.fixture
def multi_response_xml(request, remote_client):
    """Load test XML once per test session."""
    from pathlib import Path

    from hurl.models.measurement_list import HilltopMeasurementList

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
    from pathlib import Path

    from hurl.models.measurement_list import HilltopMeasurementList

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
    from pathlib import Path

    from hurl.models.measurement_list import HilltopMeasurementList

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
def units_response_xml(request, remote_client):
    """Load test XML once per test session."""
    from pathlib import Path

    from hurl.models.measurement_list import HilltopMeasurementList

    path = (
        Path(__file__).parent.parent
        / "fixture_cache"
        / "measurement_list"
        / "units_response.xml"
    )

    if request.config.getoption("--update"):
        remote_url = HilltopMeasurementList.gen_url(
            remote_client.base_url,
            remote_client.hts_endpoint,
            units="Yes",
        )
        remote_xml = remote_client.session.get(remote_url).text

        path.write_text(remote_xml, encoding="utf-8")

    raw_xml = path.read_text(encoding="utf-8")

    return raw_xml


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
        from tests.conftest import remove_tags

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
        remote_xml_cleaned = remove_tags(remote_xml, tags_to_remove)
        cached_xml_cleaned = remove_tags(cached_xml, tags_to_remove)

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

    @pytest.mark.remote
    @pytest.mark.update
    def test_units_response_xml_fixture(
        self,
        remote_client,
        units_response_xml,
    ):
        """Validate the XML units response from Hilltop Server."""
        from hurl.models.measurement_list import HilltopMeasurementList

        cached_xml = units_response_xml

        remote_url = HilltopMeasurementList.gen_url(
            remote_client.base_url,
            remote_client.hts_endpoint,
            units="Yes",
        )
        remote_xml = remote_client.session.get(remote_url).text

        assert remote_xml == cached_xml


class TestParameterValidation:
    def test_gen_measurement_list_url(self):
        """Test the URL generation for HilltopMeasurementList."""
        from urllib.parse import quote, urlencode

        from hurl.models.measurement_list import (HilltopMeasurementList,
                                                  gen_measurement_list_url)

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        correct_params = {
            "Service": "Hilltop",
            "Request": "MeasurementList",
            "Site": "River At Site",
            "Collection": "collection",
            "Units": "Yes",
            "Target": "HtmlSelect",
        }

        correct_url = (
            f"{base_url}/{hts_endpoint}?"
            f"{urlencode(correct_params, quote_via=quote)}"
        )

        test_url = gen_measurement_list_url(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            site="River At Site",
            collection="collection",
            units="Yes",
            target="HtmlSelect",
        )
        assert test_url == correct_url

        blank_url = gen_measurement_list_url(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
        )
        assert blank_url == (
            "http://example.com/foo.hts?Service=Hilltop&Request=MeasurementList"
        )

        test_method_gen_url = HilltopMeasurementList.gen_url(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            site="River At Site",
            collection="collection",
            units="Yes",
            target="HtmlSelect",
        )

        assert test_method_gen_url == correct_url

    def test_invalid_request(self):
        """Test invalid request."""
        from hurl.exceptions import HilltopRequestError
        from hurl.models.measurement_list import HilltopMeasurementList

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"
        with pytest.raises(HilltopRequestError) as excinfo:
            HilltopMeasurementList.gen_url(
                base_url=base_url,
                hts_endpoint=hts_endpoint,
                site="River At Site",
                collection="collection",
                units="Yes",
                target="HtmlSelect",
                request="InvalidRequest",
            )

    def test_invalid_units(self):
        """Test invalid units."""
        from hurl.exceptions import HilltopRequestError
        from hurl.models.measurement_list import HilltopMeasurementList
        base_url = "http://example.com"
        hts_endpoint = "foo.hts"
        with pytest.raises(HilltopRequestError) as excinfo:
            HilltopMeasurementList.gen_url(
                base_url=base_url,
                hts_endpoint=hts_endpoint,
                site="River At Site",
                collection="collection",
                units="InvalidUnits",
                target="HtmlSelect",
            )

    def test_invalid_target(self):
        """Test invalid target."""
        from hurl.exceptions import HilltopRequestError
        from hurl.models.measurement_list import HilltopMeasurementList
        base_url = "http://example.com"
        hts_endpoint = "foo.hts"
        with pytest.raises(HilltopRequestError) as excinfo:
            HilltopMeasurementList.gen_url(
                base_url=base_url,
                hts_endpoint=hts_endpoint,
                site="River At Site",
                collection="collection",
                units="Yes",
                target="InvalidTarget",
            )


class TestMeasurementList:

    def test_from_url(self, mock_hilltop_client_factory, multi_response_xml):
        """Test from_url method."""
        from urllib.parse import quote, urlencode

        import pandas as pd

        from hurl.models.measurement_list import HilltopMeasurementList

        # Set up the mock client
        mock_hilltop_client = mock_hilltop_client_factory(
            response_xml=multi_response_xml,
            status_code=200,
        )

        mock_client = mock_hilltop_client["client"]
        mock_session = mock_hilltop_client["session"]

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        test_params = {
            "Service": "Hilltop",
            "Request": "MeasurementList",
            "Site": "Manawatu At Teachers College",
        }

        test_url = (
            f"{base_url}/{hts_endpoint}?" f"{urlencode(test_params, quote_via=quote)}"
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

        print(dir(measurement_list))
        print(measurement_list.data_sources)

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

    def test_from_params(self, mock_hilltop_client_factory, multi_response_xml):
        """Test from_params method."""
        from urllib.parse import quote, urlencode

        import pandas as pd

        from hurl.models.measurement_list import HilltopMeasurementList

        # Set up the mock client
        mock_hilltop_client = mock_hilltop_client_factory(
            response_xml=multi_response_xml,
            status_code=200,
        )

        mock_client = mock_hilltop_client["client"]
        mock_session = mock_hilltop_client["session"]

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        test_params = {
            "Service": "Hilltop",
            "Request": "MeasurementList",
            "Site": "Manawatu At Teachers College",
            "Collection": "collection",
            "Units": "Yes",
            "Target": "HtmlSelect",
        }

        test_url = (
            f"{base_url}/{hts_endpoint}?" f"{urlencode(test_params, quote_via=quote)}"
        )

        measurement_list = HilltopMeasurementList.from_params(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            site="Manawatu At Teachers College",
            collection="collection",
            units="Yes",
            target="HtmlSelect",
            timeout=60,
            client=mock_client,
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
        import pandas as pd

        from hurl.models.measurement_list import HilltopMeasurementList

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
        from hurl.models.measurement_list import HilltopMeasurementList

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
        reason="Validator expected to fail upon encoutering a hilltop error response."
    )
    def test_error_from_xml(self, error_response_xml):
        """Test that the XML can be parsed into a HilltopMeasurementList object."""

        from hurl.exceptions import HilltopRequestError

        cached_xml = error_response_xml

        # Parse the XML into a HilltopMeasurementList object
        with pytest.raises(HilltopRequestError):
            measurement_list = HilltopMeasurementList.from_xml(cached_xml)

    def test_units_from_xml(self, units_response_xml):
        """Test that the XML can be parsed into a HilltopMeasurementList object."""
        from hurl.models.measurement_list import HilltopMeasurementList

        cached_xml = units_response_xml
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
                if m.name == "Groundwater"
            ),
            None,
        )
        assert sg_measurement is not None
        assert sg_measurement.name == "Groundwater"
        assert sg_measurement.units == "mm"

    def test_to_dict(self, all_response_xml):
        """Test to_dict method."""
        import xmltodict

        from hurl.models.measurement_list import HilltopMeasurementList

        site_list = HilltopMeasurementList.from_xml(all_response_xml)
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

