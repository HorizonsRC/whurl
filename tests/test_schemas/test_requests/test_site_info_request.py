"""Test file for SiteInfo Request Schema."""

import pytest


class TestParameterValidation:
    def test_SiteInfoRequest(self):
        from urllib.parse import quote, urlencode

        from whurl.schemas.requests import SiteInfoRequest

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"
        correct_params = {
            "Service": "Hilltop",
            "Request": "SiteInfo",
            "Site": "River At Site",
            "Collection": "AirTemperature",
        }

        correct_url = (
            f"{base_url}/{hts_endpoint}?"
            f"{urlencode(correct_params, quote_via=quote)}"
        )

        test_url = SiteInfoRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site="River At Site",
            collection="AirTemperature",
        ).gen_url()

        assert test_url == correct_url

    def test_invalid_request(self):
        """Test invalid request."""
        from whurl.exceptions import HilltopRequestError
        from whurl.schemas.requests import SiteInfoRequest

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"
        with pytest.raises(HilltopRequestError):
            SiteInfoRequest(
                base_url=base_url,
                hts_endpoint=hts_endpoint,
                request="InvalidRequest",
            ).gen_url()
