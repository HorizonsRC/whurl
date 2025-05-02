from pathlib import Path

import pytest
from urllib.parse import urlencode, quote

from hurl.client import HilltopClient
from hurl.exceptions import (HilltopHTTPError, HilltopParseError,
                             HilltopResponseError, HilltopRequestError)
from hurl.models.site_list import (HilltopSiteList,
                                   HilltopSiteListRequestParameters,
                                   gen_site_list_url)
from tests.conftest import remove_tags


@pytest.fixture
def all_response_xml(request, remote_client):
    """Fixture to get the full response XML for testing."""
    path = (
        Path(__file__).parent.parent
        / "fixture_cache"
        / "site_list"
        / "all_response.xml"
    )

    if request.config.getoption("--update"):
        remote_url = HilltopSiteList.gen_url(
            remote_client.base_url,
            remote_client.hts_endpoint,
        )
        remote_xml = remote_client.session.get(remote_url).text

        path.write_text(remote_xml, encoding="utf-8")

    raw_xml = path.read_text(encoding="utf-8")

    return raw_xml


class TestRemoteFixtures:
    @pytest.mark.remote
    @pytest.mark.update
    def test_all_response_xml_fixture(self, remote_client, all_response_xml):
        """Test the all_response_xml fixture."""
        # Get the remote URL
        remote_url = HilltopSiteList.gen_url(
            remote_client.base_url,
            remote_client.hts_endpoint,
        )
        # Get the remote XML
        remote_xml = remote_client.session.get(remote_url).text

        # Compare the local and remote XML
        assert all_response_xml == remote_xml


class TestParameterValidation:
    def test_gen_site_list_url(self):
        from hurl.models.site_list import HilltopSiteList, gen_site_list_url

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

        test_url = gen_site_list_url(
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
        )

        assert test_url == correct_url

    @pytest.mark.xfail(raises=HilltopRequestError)
    def test_invalid_location(self):
        """Test invalid location field raises HilltopRequestError."""

        test_url = gen_site_list_url(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            location="Not Yes or LatLong",
        )

    def test_invalid_bounding_box(self):
        """Test invalid bounding box raises HilltopRequestError."""
        # Only three coords
        with pytest.raises(HilltopRequestError):
            test_url = gen_site_list_url(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                bounding_box="2027000,5698000,2085000",
            )

        # Too many coords
        with pytest.raises(HilltopRequestError):
            test_url = gen_site_list_url(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                bounding_box="2027000,5698000,2085000,2085000,5698000,2085000,5698000",
            )

        # Invalid EPSG
        with pytest.raises(HilltopRequestError):
            test_url = gen_site_list_url(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                bounding_box="2027000,5698000,2085000,2085000,EPSG:1234",
            )

        # Only three coords and a valid EPSG
        with pytest.raises(HilltopRequestError):
            test_url = gen_site_list_url(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                bounding_box="2027000,5698000,2085000,EPSG:4326",
            )

        # A valid bounding box
        test_url = gen_site_list_url(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            bounding_box="2027000,5698000,2085000,5698001,EPSG:4326",
        )

    @pytest.mark.xfail(raises=HilltopRequestError)
    def test_invalid_target(self):
        """Test invalid target raises HilltopRequestError."""
        test_url = gen_site_list_url(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            target="Not HtmlSelect",
        )

    def test_invalid_syn_level(self):
        """Test invalid syn_level raises HilltopRequestError."""

        # Test invalid syn_level
        with pytest.raises(HilltopRequestError):
            test_url = gen_site_list_url(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                target="HtmlSelect",
                syn_level="Not 1, 2 or None",
            )

        # Test valid syn_level without target
        with pytest.raises(HilltopRequestError) as excinfo:
            test_url = gen_site_list_url(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                syn_level="2",
            )

        # Test invalid syn_level without target
        with pytest.raises(HilltopRequestError):
            test_url = gen_site_list_url(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                syn_level="3",
            )

        # Test valid everything
        test_url = gen_site_list_url(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            target="HtmlSelect",
            syn_level="2",
        )

    def test_invalid_fill_cols(self):
        """Test invalid fill_cols raises HilltopRequestError."""

        # Test invalid fill_cols
        with pytest.raises(HilltopRequestError):
            test_url = gen_site_list_url(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                site_parameters="SiteParameters",
                fill_cols="Not Yes or None",
            )

        # Test valid fill_cols without site_parameters
        with pytest.raises(HilltopRequestError):
            test_url = gen_site_list_url(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                fill_cols="Yes",
            )

        # Test invalid fill_cols without site_parameters
        with pytest.raises(HilltopRequestError):
            test_url = gen_site_list_url(
                base_url="http://example.com",
                hts_endpoint="foo.hts",
                fill_cols="Not Yes or None",
            )

        # Test valid everything
        test_url = gen_site_list_url(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            site_parameters="SiteParameters",
            fill_cols="Yes",
        )


class TestResponseValidation:
    def test_from_url(self, mock_hilltop_client_factory, all_response_xml):
        """Test from_url method."""

        # Set up the mock client
        mock_hilltop_client = mock_hilltop_client_factory(
            response_xml=all_response_xml,
            status_code=200,
        )

        mock_client = mock_hilltop_client["client"]
        mock_session = mock_hilltop_client["session"]

        test_url = "http://example.com/foo.hts?Request=SiteList&Service=Hilltop"

        site_list = HilltopSiteList.from_url(
            url=test_url,
            timeout=60,
            client=mock_client,
        )

        mock_session.get.assert_called_once_with(test_url, timeout=60)

        assert isinstance(site_list, HilltopSiteList)
        assert site_list.agency == "Horizons"

        assert len(site_list.site_list) > 0

        # Check if Manawatu at Teachers College is in the list
        assert any(
            site.name == "Manawatu at Teachers College" for site in site_list.site_list
        )

    def test_from_params(self, mock_hilltop_client_factory, all_response_xml):
        """Test from_params method."""

        # Set up the mock client
        mock_hilltop_client = mock_hilltop_client_factory(
            response_xml=all_response_xml,
            status_code=200,
        )

        mock_client = mock_hilltop_client["client"]
        mock_session = mock_hilltop_client["session"]

        site_list = HilltopSiteList.from_params(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            location="location",
            bounding_box="bounding_box",
            measurement="measurement",
            collection="collection",
            site_parameters="site_parameters",
            target="target",
            syn_level="syn_level",
            fill_cols="fill_cols",
            client=mock_client,
        )

        test_url = (
            "http://example.com/foo.hts?"
            "Service=Hilltop"
            "&Request=SiteList"
            "&Location=location"
            "&BBox=bounding_box"
            "&Measurement=measurement"
            "&Collection=collection"
            "&SiteParameters=site_parameters"
            "&Target=target"
            "&SynLevel=syn_level"
            "&FillCols=fill_cols"
        )

        mock_session.get.assert_called_once_with(
            test_url,
            timeout=60,
        )

        # Test the top level response object
        assert isinstance(site_list, HilltopSiteList)
        assert site_list.agency == "Horizons"

        assert len(site_list.site_list) > 0

        # Check if Manawatu at Teachers College is in the list
        assert any(
            site.name == "Manawatu at Teachers College" for site in site_list.site_list
        )

    def test_to_dict(self, all_response_xml):
        """Test to_dict method."""
        import xmltodict

        site_list = HilltopSiteList.from_xml(all_response_xml)
        # Convert to dictionary
        test_dict = site_list.to_dict()

        # HORRIBLE HACK because the naive xmltodict parser just makes everything strings
        test_dict = {
            k: (
                str(v)
                if not isinstance(v, list) and v is not None
                else (
                    [
                        {
                            kk: str(vv) if str(vv) != "None" else None
                            for kk, vv in i.items()
                        }
                        for i in v
                    ]
                    if isinstance(v, list)
                    else v
                )
            )
            for k, v in test_dict.items()
        }

        naive_dict = xmltodict.parse(all_response_xml)["HilltopServer"]

        assert test_dict == naive_dict
