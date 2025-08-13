"""Tests for the CollectionListResponse schema."""

import pytest


@pytest.fixture
def basic_response_xml(request, httpx_mock, remote_client):
    """Fixture for a basic CollectionListResponse XML."""
    from pathlib import Path
    from urllib.parse import urlparse

    from hurl.schemas.requests.collection_list import CollectionListRequest

    path = (
        Path(__file__).parent.parent.parent
        / "fixture_cache"
        / "collection_list"
        / "response.xml"
    )

    if request.config.getoption("--update"):

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        remote_url = CollectionListRequest(
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
    def test_basic_response_xml_fixture(
        self,
        remote_client,
        httpx_mock,
        basic_response_xml,
    ):
        """Test that the basic response XML fixture is loaded correctly."""
        from urllib.parse import urlparse

        from hurl.schemas.requests.collection_list import CollectionListRequest

        # Generate the URL for the remote request.
        remote_url = CollectionListRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
        ).gen_url()

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        remote_xml = remote_client.session.get(remote_url).text

        assert remote_xml == basic_response_xml


class TestResponseValidation:
    def test_basic_response_xml(self, httpx_mock, basic_response_xml):
        """Validate the response XML against the CollectionListResponse schema."""

        from hurl.client import HilltopClient
        from hurl.schemas.requests.collection_list import CollectionListRequest
        from hurl.schemas.responses.collection_list import CollectionListResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        test_url = CollectionListRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=basic_response_xml,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            result = client.get_collection_list()

        # Base Model
        assert isinstance(result, CollectionListResponse)
        assert result.title == "Environmental Data"

        # Check the collections
        collections = result.collections

        assert isinstance(collections, list)
        assert len(collections) > 0

        for collection in collections:
            assert isinstance(collection, CollectionListResponse.Collection)
            assert isinstance(collection.name, str)

            items = collection.items

            assert isinstance(items, list)

            for item in items:
                assert isinstance(item, CollectionListResponse.Collection.Item)
                assert isinstance(item.site_name, str)
                assert isinstance(item.measurement, str | None)
                assert isinstance(item.filename, str | None)
