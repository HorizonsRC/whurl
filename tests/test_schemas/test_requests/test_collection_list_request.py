import pytest


class TestParameterValidation:
    def test_CollectionListRequest(self):
        from urllib.parse import quote, urlencode

        from whurl.schemas.requests import CollectionListRequest

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"
        correct_params = {
            "Service": "Hilltop",
            "Request": "CollectionList",
        }

        correct_url = (
            f"{base_url}/{hts_endpoint}?"
            f"{urlencode(correct_params, quote_via=quote)}"
        )

        test_url = CollectionListRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ).gen_url()

        assert test_url == correct_url

    def test_invalid_request(self):
        """Test invalid request."""
        from whurl.exceptions import HilltopRequestError
        from whurl.schemas.requests import CollectionListRequest

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"
        with pytest.raises(HilltopRequestError):
            CollectionListRequest(
                base_url=base_url,
                hts_endpoint=hts_endpoint,
                request="InvalidRequest",
            ).gen_url()
