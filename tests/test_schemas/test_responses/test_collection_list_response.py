"""Tests for the CollectionListResponse schema."""

import os

import pytest
from dotenv import load_dotenv

load_dotenv()


def create_cached_fixtures(filename: str, request_kwargs: dict = None):
    """Factory to create cached fixtures."""

    @pytest.fixture
    def fixture_func(request, httpx_mock, remote_client):
        """Load test XML once per test session."""
        from pathlib import Path
        from urllib.parse import urlparse

        from whurl.schemas.requests.collection_list import \
            CollectionListRequest

        path = (
            Path(__file__).parent.parent.parent
            / "fixture_cache"
            / "collection_list"
            / filename
        )
        if request.config.getoption("--update"):
            # Switch off httpx mock so that cached request can go through.
            httpx_mock._options.should_mock = (
                lambda request: request.url.host
                != urlparse(remote_client.base_url).netloc
            )
            cached_url = CollectionListRequest(
                base_url=remote_client.base_url,
                hts_endpoint=remote_client.hts_endpoint,
                **(request_kwargs or {}),
            ).gen_url()
            cached_xml = remote_client.session.get(cached_url).text
            path.write_text(cached_xml, encoding="utf-8")

        # Skip gracefully if fixture cache file doesn't exist in offline mode
        if not path.exists():
            pytest.skip(
                f"Fixture cache file not found: {path.name}. Use --update flag to populate from remote API."
            )

        raw_xml = path.read_text(encoding="utf-8")
        return raw_xml

    return fixture_func


def create_mocked_fixtures(filename: str):
    """Factory to create mocked fixtures."""

    @pytest.fixture
    def fixture_func():
        """Load test XML once per test session."""
        from pathlib import Path

        path = (
            Path(__file__).parent.parent.parent
            / "mocked_data"
            / "collection_list"
            / filename
        )
        raw_xml = path.read_text(encoding="utf-8")
        return raw_xml

    return fixture_func


# Create cached fixtures
basic_response_xml_cached = create_cached_fixtures("response.xml")

# Create mocked fixtures
basic_response_xml_mocked = create_mocked_fixtures("response.xml")


class TestRemoteFixtures:
    @pytest.mark.remote
    @pytest.mark.integration
    def test_basic_response_xml_fixture(
        self,
        remote_client,
        httpx_mock,
        basic_response_xml_cached,
    ):
        """Test that the basic response XML fixture is loaded correctly."""
        from urllib.parse import urlparse

        from whurl.schemas.requests.collection_list import \
            CollectionListRequest

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

        assert remote_xml == basic_response_xml_cached


class TestResponseValidation:
    @pytest.mark.unit
    def test_basic_response_xml_unit(self, httpx_mock, basic_response_xml_mocked):
        """Validate the response XML against the CollectionListResponse schema with mocked data."""

        from whurl.client import HilltopClient
        from whurl.schemas.requests.collection_list import \
            CollectionListRequest
        from whurl.schemas.responses.collection_list import \
            CollectionListResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        test_url = CollectionListRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=basic_response_xml_mocked,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            result = client.get_collection_list()

        # Base Model
        assert isinstance(result, CollectionListResponse)
        assert result.title == "Test Project"

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

    @pytest.mark.integration
    def test_basic_response_xml_integration(
        self, httpx_mock, basic_response_xml_cached
    ):
        """Validate the response XML against the CollectionListResponse schema with cached data."""

        from whurl.client import HilltopClient
        from whurl.schemas.requests.collection_list import \
            CollectionListRequest
        from whurl.schemas.responses.collection_list import \
            CollectionListResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        test_url = CollectionListRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=basic_response_xml_cached,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            result = client.get_collection_list()

        # Base Model
        assert isinstance(result, CollectionListResponse)

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

    @pytest.mark.unit
    async def test_collection_list_with_async_client_unit(
        self, httpx_mock, basic_response_xml_mocked
    ):
        """Validate the response XML using AsyncHilltopClient."""

        from whurl.client import AsyncHilltopClient
        from whurl.schemas.requests.collection_list import \
            CollectionListRequest
        from whurl.schemas.responses.collection_list import \
            CollectionListResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        test_url = CollectionListRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=basic_response_xml_mocked,
        )

        async with AsyncHilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            result = await client.get_collection_list()

        # Base Model
        assert isinstance(result, CollectionListResponse)
        assert result.title == "Test Project"
