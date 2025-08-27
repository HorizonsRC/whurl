"""Tests for the Status response schema."""

import os

import pytest
import pytest_httpx


@pytest.fixture
def status_response_xml(request, httpx_mock, remote_client):
    """Test the status response schema."""
    from pathlib import Path
    from urllib.parse import urlparse

    from hurl.schemas.requests import StatusRequest

    path = (
        Path(__file__).parent.parent.parent
        / "fixture_cache"
        / "status"
        / "response.xml"
    )

    if request.config.getoption("--update"):

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        remote_url = StatusRequest(
            base_url=remote_client.base_url, hts_endpoint=remote_client.hts_endpoint
        ).gen_url()
        remote_xml = remote_client.session.get(remote_url).text
        path.write_text(remote_xml, encoding="utf-8")

        # httpx_mock.reset()

    raw_xml = path.read_text(encoding="utf-8")

    return raw_xml


class TestRemoteFixtures:
    @pytest.mark.remote
    @pytest.mark.update
    def test_response_xml_fixture(self, httpx_mock, remote_client, status_response_xml):
        """Validate the status response XML fixture."""
        from urllib.parse import urlparse

        from hurl.schemas.requests import StatusRequest
        from tests.conftest import remove_tags

        cached_xml = status_response_xml

        status_req = StatusRequest(
            base_url=remote_client.base_url, hts_endpoint=remote_client.hts_endpoint
        )

        remote_url = status_req.gen_url()

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        remote_xml = remote_client.session.get(remote_url).text

        tags_to_remove = [
            "ProcessID",
            "WorkingSet",
            "OpenFor",
            "FullRefresh",
            "SoftRefresh",
            "DataFile",
        ]

        # remove the tags OpenFor, FullRefresh and SoftRefresh and their contents
        remote_xml_cleaned = remove_tags(remote_xml, tags_to_remove)
        cached_xml_cleaned = remove_tags(cached_xml, tags_to_remove)

        assert remote_xml_cleaned == cached_xml_cleaned


class TestResponseValidation:

    def test_status_response(self, httpx_mock, status_response_xml):
        """Test the StatusResponse model."""

        from hurl.client import HilltopClient
        from hurl.schemas.requests import StatusRequest
        from hurl.schemas.responses import StatusResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        status_req = StatusRequest(base_url=base_url, hts_endpoint=hts_endpoint)

        test_url = status_req.gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=status_response_xml,
        )

        # Call the client as normal
        client = HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        )

        result = client.get_status()

        assert isinstance(result, StatusResponse)
        assert result.agency == "Horizons"
        assert result.script_name == os.getenv("HILLTOP_HTS_ENDPOINT")

    def test_to_dict(self, status_response_xml):
        """Test to_dict method."""
        import xmltodict

        from hurl.schemas.responses import StatusResponse

        site_list = StatusResponse.from_xml(status_response_xml)

        # Convert to dictionary
        test_dict = site_list.to_dict()

        # Convert all dict values to string for comparison
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

        naive_dict = xmltodict.parse(status_response_xml)["HilltopServer"]
        # convert the "DataFile" dict to a list of dicts
        naive_dict["DataFile"] = (
            [naive_dict["DataFile"]]
            if isinstance(naive_dict["DataFile"], dict)
            else naive_dict["DataFile"]
        )

        assert test_dict == naive_dict
