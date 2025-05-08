
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

