import pytest


@pytest.fixture
def all_response_xml(request, httpx_mock, remote_client):
    """Fixture to get the full response XML for testing."""
    from pathlib import Path
    from urllib.parse import urlparse

    from hurl.schemas.requests import SiteListRequest

    path = (
        Path(__file__).parent.parent.parent
        / "fixture_cache"
        / "site_list"
        / "all_response.xml"
    )

    if request.config.getoption("--update"):

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        remote_url = SiteListRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
        ).gen_url()
        remote_xml = remote_client.session.get(remote_url).text

        path.write_text(remote_xml, encoding="utf-8")

    raw_xml = path.read_text(encoding="utf-8")

    return raw_xml


class TestRemoteFixtures:
    @pytest.mark.remote
    @pytest.mark.update
    def test_all_response_xml_fixture(
        self, remote_client, httpx_mock, all_response_xml
    ):
        """Test the all_response_xml fixture."""
        from urllib.parse import urlparse

        from hurl.schemas.requests import SiteListRequest

        # Generate the remote URL
        remote_url = SiteListRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
        ).gen_url()

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        # Get the remote XML
        remote_xml = remote_client.session.get(remote_url).text

        # Compare the local and remote XML
        assert all_response_xml == remote_xml


class TestResponseValidation:
    def test_all_response_xml(self, httpx_mock, all_response_xml):
        """Test all_reponse_xml parsing."""

        from hurl.client import HilltopClient
        from hurl.schemas.requests import SiteListRequest
        from hurl.schemas.responses import SiteListResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        test_url = SiteListRequest(
            base_url=base_url, hts_endpoint=hts_endpoint
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=all_response_xml,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            result = client.get_site_list()

        assert isinstance(result, SiteListResponse)
        # Integration tests should only check structure and types, not specific organization names
        assert result.agency is not None
        assert isinstance(result.agency, str)

        assert len(result.site_list) > 0

        # Check if Manawatu at Teachers College is in the list
        assert any(
            site.name == "Manawatu at Teachers College" for site in result.site_list
        )

    def test_to_dict(self, all_response_xml):
        """Test to_dict method."""
        import xmltodict

        from hurl.schemas.responses import SiteListResponse

        site_list = SiteListResponse.from_xml(all_response_xml)
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
