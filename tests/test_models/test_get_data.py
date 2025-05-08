from pathlib import Path

import pandas as pd
import pytest

from hurl.client import HilltopClient
from hurl.exceptions import HilltopParseError, HilltopResponseError
from hurl.models.get_data import (HilltopData, HilltopDataSource,
                                  HilltopGetData, HilltopItemInfo)
from tests.conftest import remove_tags


class TestHilltopGetData:
    def test_gen_get_data_url(self):
        from hurl.models.get_data import gen_get_data_url

        correct_url = (
            "http://example.com/foo.hts?"
            "Request=GetData"
            "&Service=Hilltop"
            "&Site=site"
            "&Measurement=measurement"
            "&From=from_datetime"
            "&To=to_datetime"
            "&TimeInterval=time_interval"
            "&Alignment=alignment"
            "&Collection=collection"
            "&Method=method"
            "&Interval=interval"
            "&GapTolerance=gap_tolerance"
            "&ShowFinal=show_final"
            "&DateOnly=date_only"
            "&SendAs=send_as"
            "&Agency=agency"
            "&Format=format"
            "&tsType=ts_type"
            "&ShowQuality=show_quality"
        )

        test_url = gen_get_data_url(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            site="site",
            measurement="measurement",
            from_datetime="from_datetime",
            to_datetime="to_datetime",
            time_interval="time_interval",
            alignment="alignment",
            collection="collection",
            method="method",
            interval="interval",
            gap_tolerance="gap_tolerance",
            show_final="show_final",
            date_only="date_only",
            send_as="send_as",
            agency="agency",
            format="format",
            ts_type="ts_type",
            show_quality="show_quality",
        )

        assert test_url == correct_url

    def test_from_url(self, mock_hilltop_client_factory, basic_response_xml):
        """Test from_url method."""

        # Set up the mock client
        mock_hilltop_client = mock_hilltop_client_factory(
            response_xml=basic_response_xml,
            status_code=200,
        )

        mock_client = mock_hilltop_client["client"]
        mock_session = mock_hilltop_client["session"]

        test_url = (
            "http://example.com/foo.hts?"
            "Request=GetData"
            "&Service=Hilltop"
            "&Site=Manawatu%20at%20Teachers%20College"
            "&Measurement=Stage"
        )

        response_data = HilltopGetData.from_url(
            url=test_url,
            timeout=60,
            client=mock_client,
        )

        mock_session.get.assert_called_once_with(test_url, timeout=60)

        # Base Model
        assert isinstance(response_data, HilltopGetData)
        assert response_data.agency == "Horizons"

        # Measurement
        assert len(response_data.measurement) == 1
        measurement = response_data.measurement[0]
        assert measurement.site_name == "Manawatu at Teachers College"

        # Data Source
        data_source = measurement.data_source
        assert data_source.name == "Water Level"
        assert data_source.num_items == 1
        assert data_source.ts_type == "StdSeries"
        assert data_source.data_type == "SimpleTimeSeries"
        assert data_source.interpolation == "Instant"
        assert data_source.item_format is None

        # Item Info
        assert len(data_source.item_info) == 1
        item_info = data_source.item_info[0]
        assert item_info.item_number == 1
        assert item_info.item_name == "Stage"
        assert item_info.item_format == "F"
        assert item_info.units == "mm"
        assert item_info.format == "####"

        # Data
        data = measurement.data
        assert data.date_format == "Calendar"
        assert data.num_items == 1

    def test_from_params(self, mock_hilltop_client_factory, collection_response_xml):
        """Test from_params method."""
        # Set up the mock client
        mock_hilltop_client = mock_hilltop_client_factory(
            response_xml=collection_response_xml,
            status_code=200,
        )

        mock_client = mock_hilltop_client["client"]
        mock_session = mock_hilltop_client["session"]

        # Actual parameters don't matter, just gotta make sure they make it into the url
        response_data = HilltopGetData.from_params(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            collection="Rainfall",
            client=mock_client,
            timeout=60,
        )

        test_url = (
            "http://example.com/foo.hts?"
            "Request=GetData"
            "&Service=Hilltop"
            "&Collection=Rainfall"
        )

        mock_session.get.assert_called_once_with(
            test_url,
            timeout=60,
        )

        # Test the top level response object
        assert isinstance(response_data, HilltopGetData)
        assert response_data.agency == "Horizons"

        assert len(response_data.measurement) > 0

        # Find the measurement with the site_name "Kahuterawa at Scotts Road"
        measurement = next(
            (
                m
                for m in response_data.measurement
                if m.site_name == "Kahuterawa at Scotts Road"
            ),
            None,
        )
        assert measurement is not None
        assert isinstance(measurement.data_source, HilltopDataSource)

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
        assert isinstance(item_info, HilltopItemInfo)
        assert item_info.item_number == 1
        assert item_info.item_name == "Rainfall"
        assert item_info.item_format == "I"
        assert item_info.divisor is None
        assert item_info.units == "mm"
        assert item_info.format == "####.#"

        # Test the data
        data = measurement.data
        assert isinstance(data, HilltopData)
        assert data.date_format == "Calendar"
        assert data.num_items == 1
        assert isinstance(data.timeseries, pd.DataFrame)
        assert len(data.timeseries) > 0

        # Test the timeseries DataFrame
        assert data.timeseries.index.name == "DateTime"
        assert "Rainfall" in data.timeseries.columns
        assert data.timeseries.index.dtype == "datetime64[ns]"


#     def test_to_dict(self, all_response_xml):
#         """Test to_dict method."""
#         import xmltodict
#
#         site_list = HilltopSiteList.from_xml(all_response_xml)
#         # Convert to dictionary
#         test_dict = site_list.to_dict()
#
#         # HORRIBLE HACK because the naive xmltodict parser just makes everything strings
#         test_dict = {
#             k: (
#                 str(v)
#                 if not isinstance(v, list) and v is not None
#                 else (
#                     [
#                         {
#                             kk: str(vv) if str(vv) != "None" else None
#                             for kk, vv in i.items()
#                         }
#                         for i in v
#                     ]
#                     if isinstance(v, list)
#                     else v
#                 )
#             )
#             for k, v in test_dict.items()
#         }
#
#         naive_dict = xmltodict.parse(all_response_xml)["HilltopServer"]
#
#         assert test_dict == naive_dict
#
#
# def test_get_data_url():
#     base_url = "http://hilltopdev.horizons.govt.nz/boo.hts"
#     params = {
#         "site": "Manawatu at Teachers College",
#         "measurement": "Atmospheric Pressure",
#         "from_datetime": "1/1/2021",
#         "to_datetime": "2/1/2021",
#         "time_interval": "2021-01-01T12:00:00/2021-01-02T12:00:00",
#         "alignment": "Alignment=00:00",  # Align to the start of the day.
#         "collection": "AtmosphericPressure",
#         "method": "Interpolate",
#         "interval": "1day",  # ??
#         "gap_tolerance": "1week",
#         "show_final": "Yes",
#         "date_only": "Yes",
#         "send_as": "NewMeasurementName",
#         "agency": "LAWA",
#         "format": "Native",
#         "ts_type": "StdQualSeries",
#         "show_quality": "Yes",
#     }
#
#     url = get_data.get_get_data_url(base_url, **params)
#     print(url)
#
#     assert (
#         url
#         == """http://hilltopdev.horizons.govt.nz/boo.hts?Request=GetData&Service=Hilltop&Site=Manawatu%20at%20Teachers%20College&Measurement=Atmospheric%20Pressure&From=1%2F1%2F2021&To=2%2F1%2F2021&TimeInterval=2021-01-01T12%3A00%3A00%2F2021-01-02T12%3A00%3A00&Alignment=Alignment%3D00%3A00&Collection=AtmosphericPressure&Method=Interpolate&Interval=1day&GapTolerance=1week&ShowFinal=Yes&DateOnly=Yes&SendAs=NewMeasurementName&Agency=LAWA&Format=Native&tsType=StdQualSeries&ShowQuality=Yes"""
#     )
