from hurl.client import HilltopClient
from hurl.models.site_list import HilltopSiteList
from hurl.exceptions import HilltopParseError, HilltopResponseError

import pytest
from pathlib import Path
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


@pytest.fixture
def mock_hilltop_client(mocker, all_response_xml):
    """Mock HilltopClient."""
    # Mock the response
    mock_response = mocker.MagicMock()
    mock_response.text = all_response_xml
    mock_response.status_code = 200

    # Mock the session
    mock_session = mocker.MagicMock()
    mock_session.get.return_value = mock_response

    # Mock the client context manager
    mock_client = mocker.MagicMock()
    mock_client.base_url = "http://example.com"
    mock_client.hts_endpoint = "foo.hts"
    mock_client.timeout = 60
    mock_client.__enter__.return_value = mock_client  # Returns self
    mock_client.__exit__.return_value = None
    mock_client.session = mock_session

    # Patch the real client
    mocker.patch("hurl.client.HilltopClient", return_value=mock_client)

    return {
        "client": mock_client,
        "session": mock_session,
        "response": mock_response,
    }


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


class TestHilltopSiteList:
    def test_gen_site_list_url(self):
        from hurl.models.site_list import HilltopSiteList, gen_site_list_url

        correct_url = (
            "http://example.com/foo.hts?"
            "Request=SiteList"
            "&Service=Hilltop"
            "&Location=location"
            "&BoundingBox=bounding_box"
            "&Measurement=measurement"
            "&Collection=collection"
            "&SiteParameters=site_parameters"
            "&Target=target"
            "&SynLevel=syn_level"
            "&FillCols=fill_cols"
        )

        test_url = gen_site_list_url(
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
        )

        assert test_url

    def test_from_url(self, mock_hilltop_client):
        """Test from_url method."""
        mock_client = mock_hilltop_client["client"]
        mock_session = mock_hilltop_client["session"]

        test_url = "http://example.com/foo.hts?" "Request=SiteList" "&Service=Hilltop"

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

    def test_from_params(self, mock_hilltop_client):
        """Test from_params method."""
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
            "Request=SiteList"
            "&Service=Hilltop"
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
