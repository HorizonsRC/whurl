"""Test file for SiteInfo Response Schema."""

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

        from hurl.schemas.requests.site_info import SiteInfoRequest

        path = (
            Path(__file__).parent.parent.parent
            / "fixture_cache"
            / "site_info"
            / filename
        )
        if request.config.getoption("--update"):
            # Switch off httpx mock so that cached request can go through.
            httpx_mock._options.should_mock = (
                lambda request: request.url.host
                != urlparse(remote_client.base_url).netloc
            )
            cached_url = SiteInfoRequest(
                base_url=remote_client.base_url,
                hts_endpoint=remote_client.hts_endpoint,
                **(request_kwargs or {}),
            ).gen_url()
            cached_xml = remote_client.session.get(cached_url).text
            path.write_text(cached_xml, encoding="utf-8")
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
            Path(__file__).parent.parent.parent / "mocked_data" / "site_info" / filename
        )
        raw_xml = path.read_text(encoding="utf-8")
        return raw_xml

    return fixture_func


# Create cached fixtures
basic_response_xml_cached = create_cached_fixtures(
    "response.xml", {"site": os.getenv("TEST_SITE")}
)
collection_response_xml_cached = create_cached_fixtures(
    "collection_response.xml", {"collection": os.getenv("TEST_COLLECTION")}
)

# Create mocked fixtures
basic_response_xml_mocked = create_mocked_fixtures("response.xml")
collection_response_xml_mocked = create_mocked_fixtures("collection_response.xml")


class TestRemoteFixtures:
    @pytest.mark.remote
    @pytest.mark.integration
    def test_basic_response_xml_fixture(
        self,
        remote_client,
        httpx_mock,
        basic_response_xml_cached,
    ):
        """Validate the XML response from Hilltop Server."""
        from urllib.parse import urlparse

        from hurl.schemas.requests.site_info import SiteInfoRequest
        from tests.conftest import remove_tags

        # Generate the remote URL
        remote_url = SiteInfoRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            site=os.getenv("TEST_SITE"),
        ).gen_url()

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        remote_xml = remote_client.session.get(remote_url).text

        tags_to_remove = []

        # remove the tags
        remote_xml_cleaned = remove_tags(remote_xml, tags_to_remove)
        basic_response_xml_cleaned = remove_tags(
            basic_response_xml_cached, tags_to_remove
        )

        assert remote_xml_cleaned == basic_response_xml_cleaned

    @pytest.mark.remote
    @pytest.mark.integration
    def test_collection_response_xml_fixture(
        self,
        remote_client,
        httpx_mock,
        collection_response_xml_cached,
    ):
        """Validate the XML response from Hilltop Server."""
        from urllib.parse import urlparse

        from hurl.schemas.requests.site_info import SiteInfoRequest
        from tests.conftest import remove_tags

        # Generate the remote URL
        remote_url = SiteInfoRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            collection=os.getenv("TEST_COLLECTION"),
        ).gen_url()

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        remote_xml = remote_client.session.get(remote_url).text

        tags_to_remove = []

        # remove the tags
        remote_xml_cleaned = remove_tags(remote_xml, tags_to_remove)
        collection_response_xml_cleaned = remove_tags(
            collection_response_xml_cached, tags_to_remove
        )

        assert remote_xml_cleaned == collection_response_xml_cleaned


class TestResponseValidation:
    @pytest.mark.unit
    def test_basic_response_xml_unit(self, httpx_mock, basic_response_xml_mocked):
        """Validate the XML response against the SiteInfoResponse schema with mocked data."""

        import pandas as pd

        from hurl.client import HilltopClient
        from hurl.schemas.requests.site_info import SiteInfoRequest
        from hurl.schemas.responses.site_info import SiteInfoResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        test_url = SiteInfoRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site="Test Site Alpha",
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
            result = client.get_site_info(
                site="Test Site Alpha",
            )

        # Base Model
        assert isinstance(result, SiteInfoResponse)
        assert result.agency == "Test Council"

        df = result.to_dataframe()

        assert isinstance(df, pd.DataFrame)

        # SiteInfoResponse
        site = result.site[0]

        assert site.name == "Test Site Alpha"
        assert isinstance(site.info, dict)

        site_info = site.info

        assert site_info["Altitude"] == str(444)
        assert site_info["SecondSynonym"] == "WTF"

    @pytest.mark.integration
    def test_basic_response_xml_integration(
        self, httpx_mock, basic_response_xml_cached
    ):
        """Validate the XML response against the SiteInfoResponse schema with cached data."""

        import pandas as pd

        from hurl.client import HilltopClient
        from hurl.schemas.requests.site_info import SiteInfoRequest
        from hurl.schemas.responses.site_info import SiteInfoResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        test_url = SiteInfoRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site=os.getenv("TEST_SITE"),
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
            result = client.get_site_info(
                site=os.getenv("TEST_SITE"),
            )

        # Base Model
        assert isinstance(result, SiteInfoResponse)
        assert result.agency == os.getenv("TEST_AGENCY")

        df = result.to_dataframe()

        assert isinstance(df, pd.DataFrame)

        # SiteInfoResponse
        site = result.site[0]

        assert site.name == os.getenv("TEST_SITE")
        assert isinstance(site.info, dict)

    @pytest.mark.unit
    def test_collection_response_xml_unit(
        self, httpx_mock, collection_response_xml_mocked
    ):
        """Validate the XML response against the SiteInfoResponse schema with mocked data."""

        import pandas as pd

        from hurl.client import HilltopClient
        from hurl.schemas.requests.site_info import SiteInfoRequest
        from hurl.schemas.responses.site_info import SiteInfoResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        test_url = SiteInfoRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            collection="Test Collection",
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=collection_response_xml_mocked,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            result = client.get_site_info(
                collection="Test Collection",
            )

        # Base Model
        assert isinstance(result, SiteInfoResponse)
        assert result.agency == "Test Council"

        df = result.to_dataframe()
        assert isinstance(df, pd.DataFrame)

        assert len(result.site) > 0

        # SiteInfoResponse
        site = result.site[0]

        assert site.name == "Test Site Alpha"
        assert isinstance(site.info, dict)

        site_info = site.info

        assert site_info["Altitude"] == str(444)
        assert site_info["SecondSynonym"] == "WTF"

    @pytest.mark.integration
    def test_collection_response_xml_integration(
        self, httpx_mock, collection_response_xml_cached
    ):
        """Validate the XML response against the SiteInfoResponse schema with cached data."""

        import pandas as pd

        from hurl.client import HilltopClient
        from hurl.schemas.requests.site_info import SiteInfoRequest
        from hurl.schemas.responses.site_info import SiteInfoResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        test_url = SiteInfoRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            collection=os.getenv("TEST_COLLECTION"),
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=collection_response_xml_cached,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            result = client.get_site_info(
                collection=os.getenv("TEST_COLLECTION"),
            )

        # Base Model
        assert isinstance(result, SiteInfoResponse)
        assert result.agency == os.getenv("TEST_AGENCY")

        df = result.to_dataframe()
        assert isinstance(df, pd.DataFrame)

        assert len(result.site) > 1
