import pytest


class TestParameterValidation:
    def test_MeasurementListRequest(self):
        from urllib.parse import quote, urlencode

        from hurl.schemas.requests import MeasurementListRequest

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"
        correct_params = {
            "Service": "Hilltop",
            "Request": "MeasurementList",
            "Site": "site",
            "Collection": "collection",
            "Units": "Yes",
        }
        correct_url = (
            f"{base_url}/{hts_endpoint}?"
            f"{urlencode(correct_params, quote_via=quote)}"
        )
        test_url = MeasurementListRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site="site",
            collection="collection",
            units="Yes",
        ).gen_url()
        assert test_url == correct_url

    def test_invalid_request(self):
        """Test invalid request."""
        from urllib.parse import quote, urlencode

        from hurl.exceptions import HilltopRequestError
        from hurl.schemas.requests import MeasurementListRequest

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"
        with pytest.raises(HilltopRequestError):
            MeasurementListRequest(
                base_url=base_url,
                hts_endpoint=hts_endpoint,
                site="River At Site",
                collection="collection",
                units="Yes",
                target="HtmlSelect",
                request="InvalidRequest",
            ).gen_url()

    def test_invalid_units(self):
        """Test invalid units."""
        from urllib.parse import quote, urlencode

        from hurl.exceptions import HilltopRequestError
        from hurl.schemas.requests import MeasurementListRequest

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"
        with pytest.raises(HilltopRequestError):
            MeasurementListRequest(
                base_url=base_url,
                hts_endpoint=hts_endpoint,
                site="River At Site",
                collection="collection",
                units="InvalidUnits",
                target="HtmlSelect",
            ).gen_url()

    def test_invalid_target(self):
        """Test invalid target."""
        from urllib.parse import quote, urlencode

        from hurl.exceptions import HilltopRequestError
        from hurl.schemas.requests import MeasurementListRequest

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"
        with pytest.raises(HilltopRequestError):
            MeasurementListRequest(
                base_url=base_url,
                hts_endpoint=hts_endpoint,
                site="River At Site",
                collection="collection",
                units="Yes",
                target="InvalidTarget",
            ).gen_url()
