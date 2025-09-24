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

        from whurl.schemas.requests import SiteListRequest

        path = (
            Path(__file__).parent.parent.parent
            / "fixture_cache"
            / "site_list"
            / filename
        )
        if request.config.getoption("--update"):
            # Switch off httpx mock so that cached request can go through.
            httpx_mock._options.should_mock = (
                lambda request: request.url.host
                != urlparse(remote_client.base_url).netloc
            )
            cached_url = SiteListRequest(
                base_url=remote_client.base_url,
                hts_endpoint=remote_client.hts_endpoint,
                **(request_kwargs or {}),
            ).gen_url()
            cached_xml = remote_client.session.get(cached_url).text
            path.write_text(cached_xml, encoding="utf-8")

        # Skip gracefully if fixture cache file doesn't exist in offline mode
        if not path.exists():
            pytest.skip(
                f"Fixture cache file not found: {path.name}."
                f"Use --update flag to populate from remote API."
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
            Path(__file__).parent.parent.parent / "mocked_data" / "site_list" / filename
        )
        raw_xml = path.read_text(encoding="utf-8")
        return raw_xml

    return fixture_func


# Create cached fixtures
all_response_xml_cached = create_cached_fixtures("all_response.xml")
empty_response_xml_cached = create_cached_fixtures(
    "empty_response.xml", {"measurement": "NoSuchMeasurement"}
)
bbox_response_xml_cached = create_cached_fixtures(
    "bbox_response.xml",
    {
        "bbox": "-46.48797124,167.65999182,-44.73293297,168.83236546,EPSG:4326",
        "location": "LatLong",
    },
)

# Create mocked fixtures
all_response_xml_mocked = create_mocked_fixtures("all_response.xml")
error_response_xml_mocked = create_mocked_fixtures("error_response.xml")
empty_response_xml_mocked = create_mocked_fixtures("empty_response.xml")
bbox_response_xml_mocked = create_mocked_fixtures("bbox_response.xml")


class TestRemoteFixtures:
    @pytest.mark.remote
    @pytest.mark.integration
    def test_all_response_xml_fixture(
        self, remote_client, httpx_mock, all_response_xml_cached
    ):
        """Test the all_response_xml fixture."""
        from urllib.parse import urlparse

        from whurl.schemas.requests import SiteListRequest

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
        assert all_response_xml_cached == remote_xml

    @pytest.mark.remote
    @pytest.mark.integration
    def test_empty_response_xml_fixture(
        self, remote_client, httpx_mock, empty_response_xml_cached
    ):
        """Test the empty_response_xml fixture."""
        from urllib.parse import urlparse

        from whurl.schemas.requests import SiteListRequest

        # Generate the remote URL
        remote_url = SiteListRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            measurement="NoSuchMeasurement",
        ).gen_url()

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        # Get the remote XML
        remote_xml = remote_client.session.get(remote_url).text

        # Compare the local and remote XML
        assert empty_response_xml_cached == remote_xml

    @pytest.mark.remote
    @pytest.mark.integration
    def test_bbox_response_xml_fixture(
        self, remote_client, httpx_mock, bbox_response_xml_cached
    ):
        """Test the empty_response_xml fixture."""
        from urllib.parse import urlparse

        from whurl.schemas.requests import SiteListRequest

        # Generate the remote URL
        remote_url = SiteListRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            bbox="-46.48797124,167.65999182,-44.73293297,168.83236546,EPSG:4326",
            location="LatLong",
        ).gen_url()

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        # Get the remote XML
        remote_xml = remote_client.session.get(remote_url).text

        # Compare the local and remote XML
        assert bbox_response_xml_cached == remote_xml


class TestResponseValidation:
    @pytest.mark.unit
    def test_all_response_xml_unit(self, httpx_mock, all_response_xml_mocked):
        """Test all_response_xml parsing with mocked data."""

        from whurl.client import HilltopClient
        from whurl.schemas.requests import SiteListRequest
        from whurl.schemas.responses import SiteListResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        test_url = SiteListRequest(
            base_url=base_url, hts_endpoint=hts_endpoint
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=all_response_xml_mocked,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            result = client.get_site_list()

        assert isinstance(result, SiteListResponse)
        assert result.agency == "Test Agency"

        assert len(result.site_list) > 0

        # Check if Test Site Alpha is in the list (from mock data)
        assert any(site.name == "Test Site Alpha" for site in result.site_list)

    @pytest.mark.integration
    def test_all_response_xml_integration(self, httpx_mock, all_response_xml_cached):
        """Test all_response_xml parsing with cached data."""

        from whurl.client import HilltopClient
        from whurl.schemas.requests import SiteListRequest
        from whurl.schemas.responses import SiteListResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        test_url = SiteListRequest(
            base_url=base_url, hts_endpoint=hts_endpoint
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=all_response_xml_cached,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            result = client.get_site_list()

        assert isinstance(result, SiteListResponse)
        assert result.agency == os.getenv("TEST_AGENCY")

        assert len(result.site_list) > 0

        # Check if Manawatu at Teachers College is in the list
        assert any(site.name == os.getenv("TEST_SITE") for site in result.site_list)

    @pytest.mark.unit
    async def test_site_list_with_async_client_unit(
        self, httpx_mock, all_response_xml_mocked
    ):
        """Test SiteListResponse parsing with AsyncHilltopClient and mocked data."""
        from whurl.client import AsyncHilltopClient
        from whurl.schemas.requests import SiteListRequest
        from whurl.schemas.responses import SiteListResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        test_url = SiteListRequest(
            base_url=base_url, hts_endpoint=hts_endpoint
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=all_response_xml_mocked,
        )

        async with AsyncHilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            result = await client.get_site_list()

        assert isinstance(result, SiteListResponse)
        assert result.agency == "Test Agency"
        assert len(result.site_list) > 0
        # Check if Test Site Alpha is in the list (from mock data)
        assert any(site.name == "Test Site Alpha" for site in result.site_list)

    @pytest.mark.integration
    async def test_site_list_with_async_client_integration(
        self, httpx_mock, all_response_xml_cached
    ):
        """Test SiteListResponse parsing with AsyncHilltopClient and cached data."""
        import os

        from whurl.client import AsyncHilltopClient
        from whurl.schemas.requests import SiteListRequest
        from whurl.schemas.responses import SiteListResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        test_url = SiteListRequest(
            base_url=base_url, hts_endpoint=hts_endpoint
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=all_response_xml_cached,
        )

        async with AsyncHilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            result = await client.get_site_list()

        assert isinstance(result, SiteListResponse)
        assert result.agency == os.getenv("TEST_AGENCY")

        assert len(result.site_list) > 0

        # Check if Manawatu at Teachers College is in the list
        assert any(site.name == os.getenv("TEST_SITE") for site in result.site_list)

    @pytest.mark.unit
    def test_to_dict_unit(self, all_response_xml_mocked):
        """Test to_dict method with mocked data."""
        import xmltodict

        from whurl.schemas.responses import SiteListResponse

        site_list = SiteListResponse.from_xml(all_response_xml_mocked)
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

        naive_dict = xmltodict.parse(all_response_xml_mocked)["HilltopServer"]

        assert test_dict == naive_dict

        # Nested to_dict on the Site object is not called by the parent automatically.
        site = site_list.site_list[0]
        site_dict = site.to_dict()

        test_site_dict = {
            k: str(v) if v is not None else None for k, v in site_dict.items()
        }
        assert test_site_dict == naive_dict["Site"][0]

    @pytest.mark.integration
    def test_to_dict_integration(self, all_response_xml_cached):
        """Test to_dict method with cached data."""
        import xmltodict

        from whurl.schemas.responses import SiteListResponse

        site_list = SiteListResponse.from_xml(all_response_xml_cached)
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

        naive_dict = xmltodict.parse(all_response_xml_cached)["HilltopServer"]

        assert test_dict == naive_dict

        # Nested to_dict on the Site object is not called by the parent automatically.
        site = site_list.site_list[0]
        site_dict = site.to_dict()

        test_site_dict = {
            k: str(v) if v is not None else None for k, v in site_dict.items()
        }

        assert test_site_dict == naive_dict["Site"][0]

    @pytest.mark.unit
    def test_error_response_unit(self, httpx_mock, error_response_xml_mocked):
        """Test error handling with."""
        from whurl.client import HilltopClient
        from whurl.exceptions import HilltopResponseError
        from whurl.schemas.requests import SiteListRequest
        from whurl.schemas.responses import SiteListResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        test_url = SiteListRequest(
            base_url=base_url, hts_endpoint=hts_endpoint
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=error_response_xml_mocked,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            with pytest.raises(HilltopResponseError) as exc_info:
                result = client.get_site_list()

    @pytest.mark.unit
    def test_empty_response_unit(self, httpx_mock, empty_response_xml_mocked):
        """Test empty response handling."""
        from whurl.client import HilltopClient
        from whurl.exceptions import HilltopResponseError
        from whurl.schemas.requests import SiteListRequest
        from whurl.schemas.responses import SiteListResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        test_url = SiteListRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            measurement="NoSuchMeasurement",
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=empty_response_xml_mocked,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            result = client.get_site_list(measurement="NoSuchMeasurement")
        assert isinstance(result, SiteListResponse)
        assert result.site_list == []

    @pytest.mark.integration
    def test_empty_response_integration(self, httpx_mock, empty_response_xml_cached):
        """Test empty response handling."""
        from whurl.client import HilltopClient
        from whurl.exceptions import HilltopResponseError
        from whurl.schemas.requests import SiteListRequest
        from whurl.schemas.responses import SiteListResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        test_url = SiteListRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            measurement="NoSuchMeasurement",
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=empty_response_xml_cached,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            result = client.get_site_list(measurement="NoSuchMeasurement")

        assert isinstance(result, SiteListResponse)
        assert result.site_list == []

    @pytest.mark.unit
    def test_to_dataframe_unit(self, bbox_response_xml_mocked):
        """Test to_dataframe method with mocked data."""
        import pandas as pd

        from whurl.schemas.responses import SiteListResponse

        site_list = SiteListResponse.from_xml(bbox_response_xml_mocked)
        df = site_list.to_dataframe()
        assert isinstance(df, pd.DataFrame)

        assert not df.empty
        assert "@Name" in df.columns
        assert "Agency" in df.columns
        assert "Version" in df.columns

        # Check for known site from mock data
        assert "Test Site Alpha" in df["@Name"].values
