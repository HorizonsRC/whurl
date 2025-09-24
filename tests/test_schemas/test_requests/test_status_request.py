import pytest


class TestParameterValidation:
    def test_StatusRequest(self):
        from urllib.parse import quote, urlencode

        from whurl.exceptions import HilltopRequestError
        from whurl.schemas.requests import StatusRequest

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        correct_params = {
            "Service": "Hilltop",
            "Request": "Status",
        }

        correct_url = (
            f"{base_url}/{hts_endpoint}?"
            f"{urlencode(correct_params, quote_via=quote)}"
        )

        test_url = StatusRequest(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
        ).gen_url()

        assert test_url == correct_url

        with pytest.raises(HilltopRequestError):
            bad_url = StatusRequest(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                request="BadRequest",
            ).gen_url()
