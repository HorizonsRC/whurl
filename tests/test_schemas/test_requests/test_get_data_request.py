import pytest


class TestParameterValidation:
    def test_GetDataRequest(self):
        from urllib.parse import quote, urlencode

        from whurl.schemas.requests import GetDataRequest

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
        from whurl.exceptions import HilltopRequestError
        from whurl.schemas.requests import GetDataRequest

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

class TestGetDataRequestDatetimeValidation:
    """Test suite for GetDataRequest datetime validation."""

    @pytest.mark.parametrize("from_datetime,to_datetime", [
        # Valid combinations
        ("2023-09-01T00:00:00", "2023-10-01T00:00:00"),
        ("Data Start", "2023-10-01T00:00:00"),
        ("2023-09-01T00:00:00", "Data End"),
        ("2023-09-01T00:00:00", "now"),
    ], ids=[
        "valid_datetime_to_datetime",
        "data_start_to_datetime",
        "datetime_to_data_end",
        "datetime_to_now",
    ])
    def test_valid_datetime_combinations(self, from_datetime, to_datetime):
        """Test valid datetime combinations."""
        from whurl.schemas.requests.get_data import GetDataRequest
        request = GetDataRequest(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            site="site",
            measurement="measurement",
            from_datetime=from_datetime,
            to_datetime=to_datetime,
        )
        # Should not raise any exception
        request.gen_url()

    @pytest.mark.parametrize("from_datetime,to_datetime,expected_error_substring", [
        # Invalid formats
        (
            "10102023 00:00:00",
            "2023-10-10T00:00:00",
            "Error parsing from_datetime"
        ),
        (
            "2023-10-01T00:00:00",
            "10 Octover 2023 00:00",
            "Error parsing to_datetime"
        ),
        # Ordering issues
        (
            "2023-10-01T00:00:00",
            "2023-09-01T00:00:00",
            "From datetime must be before to datetime"
        ),
        # Invalid special case combinations
        (
            "2023-10-01T00:00:00",
            "Data Start",
            "Special keyword 'Data Start' cannot be used in the 'to_datetime' position."
        ),
        (
            "Data End",
            "2023-09-01T00:00:00",
            "Special keyword 'Data End' cannot be used in the 'from_datetime' position."
        ),
        (
            "now",
            "2023-09-01T00:00:00",
            "Special keyword 'now' cannot be used in the 'from_datetime' position."
        ),
    ], ids=[
        "invalid_from_datetime_format",
        "invalid_to_datetime_format",
        "to_datetime_before_from_datetime",
        "data_start_as_to_datetime",
        "data_end_as_from_datetime",
        "now_as_from_datetime",
    ])
    def test_invalid_datetime_combinations(self, from_datetime, to_datetime, expected_error_substring):
        """Test invalid datetime combinations that should raise errors."""
        from whurl.exceptions import HilltopRequestError
        from whurl.schemas.requests.get_data import GetDataRequest
        with pytest.raises(HilltopRequestError) as exc_info:
            GetDataRequest(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                site="site",
                measurement="measurement",
                from_datetime=from_datetime,
                to_datetime=to_datetime,
            ).gen_url()
        
        # Optional: verify the error message contains expected substring
        assert expected_error_substring.lower() in str(exc_info.value).lower()


class TestGetDataRequestTimeIntervalValidation:
    """Test suite for GetDataRequest time interval validation."""

    @pytest.mark.parametrize("time_interval", [
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
        # Invalid duration format by itself (missing T for time part)
        "P3H",
        # Impossible <start> time in <start>/<end>
        "20231232T00:00/20231202T00:00",
        # Impossible <end> time in <start>/<end>
        "20231201T00:00/20231302T00:00",
        # Impossible <start> time in <start>/<duration>
        "20231232T00:00/P3D",
        # Impossible <end> time in <duration>/<end>
        "P3D/20231302T00:00",
        # "Data Start" as <end> (invalid)
        "2023-12-01T00:00:00/Data Start",
        # "Data End" as <start> (invalid)
        "Data End/2023-12-01T00:00:00",
        # "now" as <start> (invalid)
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
    ], ids=[
        "invalid_datetime_format_start_end",
        "invalid_duration_duration_end",
        "invalid_duration_start_duration",
        "invalid_datetime_format_duration_end",
        "invalid_datetime_format_start_duration",
        "invalid_duration_standalone",
        "impossible_start_time",
        "impossible_end_time",
        "impossible_start_time_with_duration",
        "impossible_end_time_with_duration",
        "data_start_as_end",
        "data_end_as_start",
        "now_as_start",
        "impossible_start_with_data_end",
        "impossible_start_with_now",
        "impossible_end_with_data_start",
        "invalid_start_format_with_data_end",
        "invalid_start_format_with_now",
        "invalid_end_format_with_data_start",
        "end_before_start",
    ])
    def test_invalid_time_intervals(self, time_interval):
        """Test various invalid time intervals that should raise errors."""
        from whurl.exceptions import HilltopRequestError
        from whurl.schemas.requests.get_data import GetDataRequest
        with pytest.raises(HilltopRequestError):
            GetDataRequest(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                site="site",
                measurement="measurement",
                time_interval=time_interval,
            ).gen_url()

    @pytest.mark.parametrize("time_interval,expected_interval", [
        # <start>/<end>
        ("2023-10-01T00:00:00/2023-10-10T00:00:00", 
         "2023-10-01T00:00:00/2023-10-10T00:00:00"),
        # <start>/<duration>
        ("2023-10-01T00:00:00/P1D", 
         "2023-10-01T00:00:00/P1D"),
        # <duration>/<end>
        ("P1D/2023-10-10T00:00:00", 
         "P1D/2023-10-10T00:00:00"),
        # Data Start/<end>
        ("Data Start/2023-10-10T00:00:00", 
         "Data Start/2023-10-10T00:00:00"),
        # <start>/Data End
        ("2023-10-10T00:00:00/Data End", 
         "2023-10-10T00:00:00/Data End"),
        # <start>/now
        ("2023-10-10T00:00:00/now", 
         "2023-10-10T00:00:00/now"),
        # Data Start/Data End
        ("Data Start/Data End", 
         "Data Start/Data End"),
        # Data Start/now
        ("Data Start/now", 
         "Data Start/now"),
    ], ids=[
        "start_end",
        "start_duration",
        "duration_end",
        "data_start_end",
        "start_data_end",
        "start_now",
        "data_start_data_end",
        "data_start_now",
    ])
    def test_valid_interval_combinations(self, time_interval, expected_interval):
        """Test various valid interval combinations."""
        from urllib.parse import quote, urlencode
        from whurl.schemas.requests.get_data import GetDataRequest
        base_url = "http://example.com"
        hts_endpoint = "foo.hts"
        
        # Build expected URL
        correct_params = {
            "Service": "Hilltop",
            "Request": "GetData",
            "Site": "site",
            "Measurement": "measurement",
            "TimeInterval": expected_interval,
        }
        correct_url = (
            f"{base_url}/{hts_endpoint}?"
            f"{urlencode(correct_params, quote_via=quote)}"
        )
        
        # Generate test URL
        test_url = GetDataRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site="site",
            measurement="measurement",
            time_interval=time_interval,
        ).gen_url()
        
        assert test_url == correct_url

    @pytest.mark.parametrize("duration", [
        "P1Y",      # 1 year
        "P10Y",     # 10 years
        "P3M",      # 3 months
        "P3D",      # 3 days
        "P1Y3M",    # 1 year and 3 months
        "PT3H",     # 3 hours
        "PT10M",    # 10 minutes
        "PT30S",    # 30 seconds
        "P3MT30M",  # 3 months and 30 minutes
    ], ids=[
        "1_year",
        "10_years",
        "3_months",
        "3_days",
        "1_year_3_months",
        "3_hours",
        "10_minutes",
        "30_seconds",
        "3_months_30_minutes",
    ])
    def test_valid_standalone_durations(self, duration):
        """Test various valid standalone durations."""
        from urllib.parse import quote, urlencode
        from whurl.schemas.requests.get_data import GetDataRequest
        
        base_url = "http://example.com"
        hts_endpoint = "foo.hts"
        
        # Build expected URL
        correct_params = {
            "Service": "Hilltop",
            "Request": "GetData",
            "Site": "site",
            "Measurement": "measurement",
            "TimeInterval": duration,
        }
        correct_url = (
            f"{base_url}/{hts_endpoint}?"
            f"{urlencode(correct_params, quote_via=quote)}"
        )
        
        # Generate test URL
        test_url = GetDataRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site="site",
            measurement="measurement",
            time_interval=duration,
        ).gen_url()
        
        assert test_url == correct_url
       

class TestGetDataRequestAlignmentValidation:
    """Test suite for GetDataRequest alignment validation."""

    @pytest.mark.parametrize("alignment", [
        "00:00",
        "00:01",
        "00:00:00",
        "15:15:30",
        "1 week",
        "1 d",
        "3h",
        "4 months",
    ], ids=[
        "hh_mm",
        "hh_mm_with_minutes",
        "hh_mm_ss",
        "hh_mm_ss_with_values",
        "1_week",
        "1_day",
        "3_hours",
        "4_months",
    ])
    def test_valid_alignments(self, alignment):
        """Test various valid alignment formats."""
        from urllib.parse import quote, urlencode
        from whurl.schemas.requests.get_data import GetDataRequest
        
        # Should not raise any exception
        GetDataRequest(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            site="site",
            measurement="measurement",
            time_interval="Data Start/now",
            alignment=alignment,
        ).gen_url()

    @pytest.mark.parametrize("alignment", [
        "00:00:00:00",
        "2023-10-01",
        "15 parsecs",
        "Yes please",
    ], ids=[
        "invalid_time_format",
        "date_instead_of_time",
        "invalid_units",
        "gibberish",
    ])
    def test_invalid_alignments(self, alignment):
        """Test various invalid alignment formats that should raise errors."""
        from whurl.schemas.requests.get_data import GetDataRequest
        from whurl.exceptions import HilltopRequestError
        
        with pytest.raises(HilltopRequestError):
            GetDataRequest(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                site="site",
                measurement="measurement",
                time_interval="Data Start/now",
                alignment=alignment,
            ).gen_url()
            

class TestGetDataRequestMethodValidation:
    """Test suite for GetDataRequest method validation."""

    @pytest.mark.parametrize("method,interval,gap_tolerance,show_final,date_only,send_as", [
        # Valid method: Interpolate
        ("Interpolate", None, "3h", "Yes", "Yes", "TestAverage"),
        # Valid method: Average
        ("Average", "4 weeks", "3h", "Yes", "Yes", "TestAverage"),
        # Valid method: Total
        ("Total", "4 weeks", "3h", "Yes", None, "TestAverage"),
        # Valid method: Moving Average
        ("Moving Average", "4 weeks", "1 second", "Yes", "Yes", "TestAverage"),
        # Valid method: EP
        ("EP", None, "1 week", None, "Yes", None),
        # Valid method: Extrema
        ("Extrema", "4 weeks", "12h", None, "Yes", "TestAverage"),
    ], ids=[
        "interpolate",
        "average",
        "total",
        "moving_average",
        "ep",
        "extrema",
    ])
    def test_valid_methods(self, method, interval, gap_tolerance, show_final, date_only, send_as):
        """Test various valid method combinations."""
        from whurl.schemas.requests.get_data import GetDataRequest
        # Should not raise any exception
        GetDataRequest(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            site="site",
            measurement="measurement",
            time_interval="Data Start/now",
            method=method,
            interval=interval,
            gap_tolerance=gap_tolerance,
            show_final=show_final,
            date_only=date_only,
            send_as=send_as,
        ).gen_url()

    @pytest.mark.parametrize("method,interval,gap_tolerance,show_final,date_only,send_as,expected_error", [
        # Invalid method name
        (
            "InvalidMethod", None, "3h", "Yes", "Yes", None,
            "Invalid method"
        ),
        # Average requires interval
        (
            "Average", None, None, None, None, None,
            "interval required"
        ),
        # Missing method with interval
        (
            None, "4 weeks", None, None, None, "TestAverage",
            "method required"
        ),
        # Missing method and interval
        (
            None, None, "3h", None, None, "TestAverage",
            "method required"
        ),
    ], ids=[
        "invalid_method_name",
        "average_requires_interval",
        "missing_method_with_interval",
        "missing_method_and_interval",
    ])
    def test_invalid_methods(self, method, interval, gap_tolerance, show_final, date_only, send_as, expected_error):
        """Test various invalid method combinations that should raise errors."""
        from whurl.exceptions import HilltopRequestError
        from whurl.schemas.requests.get_data import GetDataRequest
        with pytest.raises(HilltopRequestError) as exc_info:
            GetDataRequest(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                site="site",
                measurement="measurement",
                time_interval="Data Start/now",
                method=method,
                interval=interval,
                gap_tolerance=gap_tolerance,
                show_final=show_final,
                date_only=date_only,
                send_as=send_as,
            ).gen_url()
        
        # Optional: verify error message contains expected substring
        assert expected_error.lower() in str(exc_info.value).lower()
