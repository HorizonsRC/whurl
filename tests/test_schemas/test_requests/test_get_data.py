import pytest


class TestParameterValidation:
    def test_GetDataRequest(self):
        from urllib.parse import quote, urlencode

        from hurl.schemas.requests import GetDataRequest

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        correct_params = {
            "Service": "Hilltop",
            "Request": "GetData",
            "Site": "site",
            "Measurement": "measurement",
            "From": "from",
            "To": "to",
            "TimeInterval": "time_interval",
            "Alignment": "alignment",
            "Collection": "collection",
            "Method": "method",
            "Interval": "interval",
            "GapTolerance": "gap_tolerance",
            "ShowFinal": "show_final",
            "DateOnly": "date_only",
            "SendAs": "send_as",
            "Agency": "agency",
            "Format": "format",
            "TSType": "ts_type",
            "ShowQuality": "show_quality",
        }

        correct_url = (
            f"{base_url}/{hts_endpoint}?"
            f"{urlencode(correct_params, quote_via=quote)}"
        )

        test_url = GetDataRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site="site",
            measurement="measurement",
            from_datetime="from",
            to_datetime="to",
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
        ).gen_url()

        assert test_url == correct_url
