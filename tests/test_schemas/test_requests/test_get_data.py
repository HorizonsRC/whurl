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
            "From": "2023-10-01T00:00:00",
            "To": "2023-10-10T00:00:00",
            "TimeInterval": "Data Start/now",
            "Alignment": "00:00",
            "Collection": "collection",
            "Method": "Average",
            "Interval": "4 weeks",
            "GapTolerance": "3h",
            "ShowFinal": "Yes",
            "DateOnly": "Yes",
            "SendAs": "send_as",
            "Agency": "agency",
            "Format": "Native",
            "TSType": "StdQualSeries",
            "ShowQuality": "Yes",
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
            from_datetime="2023-10-01T00:00:00",
            to_datetime="2023-10-10T00:00:00",
            time_interval="Data Start/now",
            alignment="00:00",
            collection="collection",
            method="Average",
            interval="4 weeks",
            gap_tolerance="3h",
            show_final="Yes",
            date_only="Yes",
            send_as="send_as",
            agency="agency",
            format="Native",
            ts_type="StdQualSeries",
            show_quality="Yes",
        ).gen_url()

        assert test_url == correct_url

    def test_invalid_request(self):
        """Test invalid request."""
        from hurl.exceptions import HilltopRequestError
        from hurl.schemas.requests import GetDataRequest

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"
        with pytest.raises(HilltopRequestError):
            GetDataRequest(
                base_url=base_url,
                hts_endpoint=hts_endpoint,
                site="River At Site",
                measurement="collection",
                request="InvalidRequest",
            ).gen_url()

    def test_datetime_validation(self):
        """Test datetime validation."""
        from hurl.exceptions import HilltopRequestError
        from hurl.schemas.requests import GetDataRequest

        # Valid Everything
        GetDataRequest(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            site="site",
            measurement="measurement",
            from_datetime="2023-09-01T00:00:00",
            to_datetime="2023-10-01T00:00:00",
        ).gen_url()

        # Valid Data Start
        GetDataRequest(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            site="site",
            measurement="measurement",
            from_datetime="Data Start",
            to_datetime="2023-10-01T00:00:00",
        ).gen_url()

        # Valid Data End
        GetDataRequest(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            site="site",
            measurement="measurement",
            from_datetime="2023-09-01T00:00:00",
            to_datetime="Data End",
        ).gen_url()

        # Valid now
        GetDataRequest(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            site="site",
            measurement="measurement",
            from_datetime="2023-09-01T00:00:00",
            to_datetime="now",
        ).gen_url()

        with pytest.raises(HilltopRequestError):
            GetDataRequest(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                site="site",
                measurement="measurement",
                from_datetime="10-01-2023 00:00:00",  # Invalid format
                to_datetime="2023-10-10T00:00:00",
            ).gen_url()

        with pytest.raises(HilltopRequestError):
            GetDataRequest(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                site="site",
                measurement="measurement",
                from_datetime="2023-10-01T00:00:00",
                to_datetime="2023-10-10 00:00",  # Invalid format
            ).gen_url()

        with pytest.raises(HilltopRequestError):
            GetDataRequest(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                site="site",
                measurement="measurement",
                from_datetime="2023-10-01T00:00:00",
                to_datetime="2023-09-01T00:00:00",  # to_datetime before from_datetime
            ).gen_url()

        with pytest.raises(HilltopRequestError):
            GetDataRequest(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                site="site",
                measurement="measurement",
                from_datetime="2023-10-01T00:00:00",
                to_datetime="Data Start",  # Data Start as to_datetime
            ).gen_url()

        with pytest.raises(HilltopRequestError):
            GetDataRequest(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                site="site",
                measurement="measurement",
                from_datetime="Data End",  # Data End as from_datetime
                to_datetime="2023-09-01T00:00:00",
            ).gen_url()

        with pytest.raises(HilltopRequestError):
            GetDataRequest(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                site="site",
                measurement="measurement",
                from_datetime="now",  # "now" as from_datetime
                to_datetime="2023-09-01T00:00:00",
            ).gen_url()

    def test_time_interval_validation_failures(self):
        """Test datetime validation."""
        from hurl.exceptions import HilltopRequestError
        from hurl.schemas.requests import GetDataRequest

        test_intervals = [
            # Invalid time format in <start>/<end>
            "10-01-2023 00:00:00/2023-10-01T00:00:00",
            # Invalid duration format in <duration>/<end>
            "P1DF/2023-10-01T00:00:00",
            # Invalid duration format in <start>/<duration>
            "2023-10-01T00:00:00/P3KKT3H",
            # Invalid time format in <duration>/<end>
            "P3M/23-10-01 00:00:00",
            # Invalid time format in <start>/<duration>
            "23/12/01T00:00/PT3H",
            # Invalid duration format by itself
            "P3H",
            # Impossible <start> time in <start>/<end>
            "20231232T00:00/20231202T00:00",
            # Impossible <end> time in <start>/<end>
            "20231201T00:00/20231302T00:00",
            # Impossible <start> time in <start>/<duration>
            "20231232T00:00/P3D",
            # Impossible <end> time in <duration>/<end>
            "P3D/20231302T00:00",
            # "Data Start" as <end>
            "2023-12-01T00:00:00/Data Start",
            # "Data End" as <start>
            "Data End/2023-12-01T00:00:00",
            # "now" as <start>
            "now/2023-12-01T00:00:00",
            # Impossible <start> time in <start>/Data End
            "20231232T00:00/Data End",
            # Impossible <start> time in <start>/now
            "20231432T00:00/now",
            # Impossible <end> time in Data Start/<end>
            "Data Start/20231232T00:00",
            # Invalid <start> time format in <start>/Data End
            "23 12 02T00:00:00/Data End",
            # Invalid <start> time format in <start>/now
            "2023.12.30T00:00/now",
            # Invalid <end> time format in Data Start/<end>
            "Data Start/2023/12/21T00:00",
            # <end> before <start>
            "2023-10-01T00:00:00/2023-09-01T00:00:00",
        ]

        for tint in test_intervals:
            with pytest.raises(HilltopRequestError):
                GetDataRequest(
                    base_url="http://example.com",
                    hts_endpoint="foo.hts",
                    site="site",
                    measurement="measurement",
                    time_interval=tint,
                ).gen_url()

    def test_time_interval_validation_success(self):
        from urllib.parse import quote, urlencode

        from hurl.schemas.requests import GetDataRequest

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        def get_urls(time_interval_string):
            correct_params = {
                "Service": "Hilltop",
                "Request": "GetData",
                "Site": "site",
                "Measurement": "measurement",
                "TimeInterval": time_interval_string,
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
                time_interval=time_interval_string,
            ).gen_url()
            return correct_url, test_url

        # <start>/<end>
        time_interval_string = "2023-10-01T00:00:00/2023-10-10T00:00:00"
        correct_url, test_url = get_urls(time_interval_string)
        assert test_url == correct_url

        # <start>/<duration>
        time_interval_string = "2023-10-01T00:00:00/P1D"
        correct_url, test_url = get_urls(time_interval_string)
        assert test_url == correct_url

        # <duration>/<end>
        time_interval_string = "P1D/2023-10-10T00:00:00"
        correct_url, test_url = get_urls(time_interval_string)
        assert test_url == correct_url

        # Data Start/<end>
        time_interval_string = "Data Start/2023-10-10T00:00:00"
        correct_url, test_url = get_urls(time_interval_string)
        assert test_url == correct_url

        # <start>/Data End
        time_interval_string = "2023-10-10T00:00:00/Data End"
        correct_url, test_url = get_urls(time_interval_string)
        assert test_url == correct_url

        # <start>/now
        time_interval_string = "2023-10-10T00:00:00/now"
        correct_url, test_url = get_urls(time_interval_string)
        assert test_url == correct_url

        # Data Start/Data End
        time_interval_string = "Data Start/Data End"
        correct_url, test_url = get_urls(time_interval_string)
        assert test_url == correct_url

        # Data Start/now
        time_interval_string = "Data Start/now"
        correct_url, test_url = get_urls(time_interval_string)
        assert test_url == correct_url

        # <duration>
        test_durations = [
            "P1Y",  # 1 day
            "P10Y",  # 1 week
            "P3M",  # 3 months
            "P3D",  # 3 days
            "P1Y3M",  # 1 year and 3 months
            "PT3H",  # 3 hours
            "PT10M",  # 10 minutes
            "PT30S",  # 30 seconds
            "P3MT30M",  # 3 months and 30 minutes, because you might need to
        ]

        for dur in test_durations:
            time_interval_string = dur
            correct_url, test_url = get_urls(time_interval_string)
            assert test_url == correct_url

    def test_alignment(self):
        """Test alignment."""
        from hurl.exceptions import HilltopRequestError
        from hurl.schemas.requests import GetDataRequest

        test_alignments = [
            "00:00",
            "00:01",
            "00:00:00",
            "15:15:30",
            "1 week",
            "1 d",
            "3h",
            "4 months",
        ]
        for alignment in test_alignments:
            # Valid alignment
            GetDataRequest(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                site="site",
                measurement="measurement",
                time_interval="Data Start/now",
                alignment=alignment,
            ).gen_url()

        invalid_alignments = [
            "00:00:00:00",
            "2023-10-01",
            "15 parsecs",
            "Yes please",
        ]
        with pytest.raises(HilltopRequestError):
            for alignment in invalid_alignments:
                GetDataRequest(
                    base_url="http://example.com",
                    hts_endpoint="foo.hts",
                    site="site",
                    measurement="measurement",
                    time_interval="Data Start/now",
                    alignment=alignment,
                ).gen_url()

    def test_method(self):
        """Test Method."""
        from hurl.exceptions import HilltopRequestError
        from hurl.schemas.requests import GetDataRequest

        # Valid methods
        valid_methods = [
            {
                "method": "Interpolate",
                "interval": None,
                "gap_tolerance": "3h",
                "show_final": "Yes",
                "date_only": "Yes",
                "send_as": "TestAverage",
            },
            {
                "method": "Average",
                "interval": "4 weeks",
                "gap_tolerance": "3h",
                "show_final": "Yes",
                "date_only": "Yes",
                "send_as": "TestAverage",
            },
            {
                "method": "Total",
                "interval": "4 weeks",
                "gap_tolerance": "3h",
                "show_final": "Yes",
                "date_only": None,
                "send_as": "TestAverage",
            },
            {
                "method": "Moving Average",
                "interval": "4 weeks",
                "gap_tolerance": "1 second",
                "show_final": "Yes",
                "date_only": "Yes",
                "send_as": "TestAverage",
            },
            {
                "method": "EP",
                "interval": None,
                "gap_tolerance": "1 week",
                "show_final": None,
                "date_only": "Yes",
                "send_as": None,
            },
            {
                "method": "Extrema",
                "interval": "4 weeks",
                "gap_tolerance": "12h",
                "show_final": None,
                "date_only": "Yes",
                "send_as": "TestAverage",
            },
        ]

        for method in valid_methods:
            GetDataRequest(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                site="site",
                measurement="measurement",
                time_interval="Data Start/now",
                method=method["method"],
                interval=method["interval"],
                gap_tolerance=method["gap_tolerance"],
                show_final=method["show_final"],
                date_only=method["date_only"],
                send_as=method["send_as"],
            ).gen_url()

        # Invalid methods
        invalid_methods = [
            {
                "method": "InvalidMethod",
                "interval": None,
                "gap_tolerance": "3h",
                "show_final": "Yes",
                "date_only": "Yes",
                "send_as": None,
            },
            {
                "method": "Average",
                "interval": None,
                "gap_tolerance": None,
                "show_final": None,
                "date_only": None,
                "send_as": None,
            },
            {
                "method": None,
                "interval": "4 weeks",
                "gap_tolerance": None,
                "show_final": None,
                "date_only": None,
                "send_as": "TestAverage",
            },
            {
                "method": None,
                "interval": None,
                "gap_tolerance": "3h",
                "show_final": None,
                "date_only": None,
                "send_as": "TestAverage",
            },
        ]

        for method in invalid_methods:
            with pytest.raises(HilltopRequestError):
                GetDataRequest(
                    base_url="http://example.com",
                    hts_endpoint="foo.hts",
                    site="site",
                    measurement="measurement",
                    time_interval="Data Start/now",
                    method=method["method"],
                    interval=method["interval"],
                    gap_tolerance=method["gap_tolerance"],
                    show_final=method["show_final"],
                    date_only=method["date_only"],
                    send_as=method["send_as"],
                ).gen_url()
