import pytest


class TestParameterValidation:
    def test_SiteListRequest(self):
        from urllib.parse import quote, urlencode

        from hurl.schemas.requests import SiteListRequest

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        correct_params = {
            "Service": "Hilltop",
            "Request": "SiteList",
            "Location": "Yes",
            "BBox": "1223456,1234567,1234567,1234667,EPSG:4326",
            "Measurement": "measurement",
            "Collection": "collection",
            "SiteParameters": "site_parameters",
            "Target": "HtmlSelect",
            "SynLevel": "2",
            "FillCols": "Yes",
        }

        correct_url = (
            f"{base_url}/{hts_endpoint}?"
            f"{urlencode(correct_params, quote_via=quote)}"
        )

        test_url = SiteListRequest(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            location="Yes",
            bounding_box="1223456,1234567,1234567,1234667,EPSG:4326",
            measurement="measurement",
            collection="collection",
            site_parameters="site_parameters",
            target="HtmlSelect",
            syn_level="2",
            fill_cols="Yes",
        ).gen_url()

        assert test_url == correct_url

    def test_invalid_location(self):
        """Test invalid location field raises HilltopRequestError."""
        from hurl.exceptions import HilltopRequestError
        from hurl.schemas.requests import SiteListRequest

        with pytest.raises(HilltopRequestError):
            test_url = SiteListRequest(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                location="Not Yes or LatLong",
            ).gen_url()

    def test_invalid_bounding_box(self):
        """Test invalid bounding box raises HilltopRequestError."""
        from hurl.exceptions import HilltopRequestError
        from hurl.schemas.requests import SiteListRequest

        # Only three coords
        with pytest.raises(HilltopRequestError):
            test_url = SiteListRequest(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                bounding_box="2027000,5698000,2085000",
            ).gen_url()

        # Too many coords
        with pytest.raises(HilltopRequestError):
            test_url = SiteListRequest(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                bounding_box="2027000,5698000,2085000,2085000,5698000,2085000,5698000",
            ).gen_url()

        # Invalid EPSG
        with pytest.raises(HilltopRequestError):
            test_url = SiteListRequest(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                bounding_box="2027000,5698000,2085000,2085000,EPSG:1234",
            ).gen_url()

        # Only three coords and a valid EPSG
        with pytest.raises(HilltopRequestError):
            test_url = SiteListRequest(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                bounding_box="2027000,5698000,2085000,EPSG:4326",
            ).gen_url()

        # A valid bounding box
        test_url = SiteListRequest(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            bounding_box="2027000,5698000,2085000,5698001,EPSG:4326",
        ).gen_url()

    def test_invalid_target(self):
        """Test invalid target raises HilltopRequestError."""
        from hurl.exceptions import HilltopRequestError
        from hurl.schemas.requests import SiteListRequest

        with pytest.raises(HilltopRequestError):
            test_url = SiteListRequest(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                target="Not HtmlSelect",
            ).gen_url()

    def test_invalid_syn_level(self):
        """Test invalid syn_level raises HilltopRequestError."""
        from hurl.exceptions import HilltopRequestError
        from hurl.schemas.requests import SiteListRequest

        # Test invalid syn_level
        with pytest.raises(HilltopRequestError):
            test_url = SiteListRequest(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                target="HtmlSelect",
                syn_level="Not 1, 2 or None",
            ).gen_url()

        # Test valid syn_level without target
        with pytest.raises(HilltopRequestError) as excinfo:
            test_url = SiteListRequest(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                syn_level="2",
            ).gen_url()

        # Test invalid syn_level without target
        with pytest.raises(HilltopRequestError):
            test_url = SiteListRequest(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                syn_level="3",
            ).gen_url()

        # Test valid everything
        test_url = SiteListRequest(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            target="HtmlSelect",
            syn_level="2",
        ).gen_url()

    def test_invalid_fill_cols(self):
        """Test invalid fill_cols raises HilltopRequestError."""
        from hurl.exceptions import HilltopRequestError
        from hurl.schemas.requests import SiteListRequest

        # Test invalid fill_cols
        with pytest.raises(HilltopRequestError):
            test_url = SiteListRequest(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                site_parameters="SiteParameters",
                fill_cols="Not Yes or None",
            ).gen_url()

        # Test valid fill_cols without site_parameters
        with pytest.raises(HilltopRequestError):
            test_url = SiteListRequest(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                fill_cols="Yes",
            ).gen_url()

        # Test invalid fill_cols without site_parameters
        with pytest.raises(HilltopRequestError):
            test_url = SiteListRequest(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                fill_cols="Not Yes or None",
            ).gen_url()

        # Test valid everything
        test_url = SiteListRequest(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            site_parameters="SiteParameters",
            fill_cols="Yes",
        ).gen_url()
