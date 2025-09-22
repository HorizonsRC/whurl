import pytest


class TestParameterValidation:
    def test_TimeRangeRequest(self):
        from urllib.parse import quote, urlencode

        from whurl.schemas.requests import TimeRangeRequest

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        correct_params = {
            "Service": "Hilltop",
            "Request": "TimeRange",
            "Site": "site",
            "Measurement": "measurement",
            "Format": "JSON",
        }

        correct_url = (
            f"{base_url}/{hts_endpoint}?"
            f"{urlencode(correct_params, quote_via=quote)}"
        )

        test_url = TimeRangeRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site="site",
            measurement="measurement",
            format="JSON",
        ).gen_url()

        assert test_url == correct_url

    def test_invalid_request(self):
        """Test invalid request."""
        from whurl.exceptions import HilltopRequestError
        from whurl.schemas.requests import TimeRangeRequest

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        with pytest.raises(HilltopRequestError):
            url = TimeRangeRequest(
                base_url=base_url,
                hts_endpoint=hts_endpoint,
                site="River At Site",
                measurement="measurement",
                request="InvalidRequest",
            ).gen_url()

    def test_no_site(self):
        """Test request without site."""
        from whurl.exceptions import HilltopRequestError
        from whurl.schemas.requests import TimeRangeRequest

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"
        with pytest.raises(HilltopRequestError):
            TimeRangeRequest(
                base_url=base_url,
                hts_endpoint=hts_endpoint,
                measurement="measurement",
            ).gen_url()

    def test_no_measurement(self):
        """Test request without measurement."""
        from whurl.exceptions import HilltopRequestError
        from whurl.schemas.requests import TimeRangeRequest

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"
        with pytest.raises(HilltopRequestError):
            TimeRangeRequest(
                base_url=base_url,
                hts_endpoint=hts_endpoint,
                site="site",
            ).gen_url()

    def test_bad_format(self):
        """Test request with bad format."""
        from whurl.exceptions import HilltopRequestError
        from whurl.schemas.requests import TimeRangeRequest

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"
        with pytest.raises(HilltopRequestError):
            TimeRangeRequest(
                base_url=base_url,
                hts_endpoint=hts_endpoint,
                site="site",
                measurement="measurement",
                format="InvalidFormat",
            ).gen_url()
