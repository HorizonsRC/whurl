"""Test file for SiteInfo Response Schema."""

import pytest


@pytest.fixture
def basic_response_xml(request, httpx_mock, remote_client):
    """Load test XML once per test session."""
    from pathlib import Path
    from urllib.parse import urlparse

    from hurl.schemas.requests.site_info import SiteInfoRequest
    from pydantic import ValidationError

    path = (
        Path(__file__).parent.parent.parent
        / "fixture_cache"
        / "site_info"
        / "response.xml"
    )

    if request.config.getoption("--update"):
        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        try:
            remote_url = SiteInfoRequest(
                base_url=remote_client.base_url,
                hts_endpoint=remote_client.hts_endpoint,
                site="Ngahere Park Climate Station",
            ).gen_url()
        except ValidationError as e:
            pytest.fail(f"Failed to generate remote URL: {e}")
        remote_xml = remote_client.session.get(remote_url).text

        path.write_text(remote_xml, encoding="utf-8")

    raw_xml = path.read_text(encoding="utf-8")

    return raw_xml


@pytest.fixture
def collection_response_xml(request, httpx_mock, remote_client):
    """Load test XML once per test session."""
    from pathlib import Path
    from urllib.parse import urlparse

    from hurl.schemas.requests.site_info import SiteInfoRequest
    from pydantic import ValidationError

    path = (
        Path(__file__).parent.parent.parent
        / "fixture_cache"
        / "site_info"
        / "collection_response.xml"
    )

    if request.config.getoption("--update"):
        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        try:
            remote_url = SiteInfoRequest(
                base_url=remote_client.base_url,
                hts_endpoint=remote_client.hts_endpoint,
                collection="AirTemperature",
            ).gen_url()
        except ValidationError as e:
            pytest.fail(f"Failed to generate remote URL: {e}")
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
        """Validate the XML response from Hilltop Server."""
        from urllib.parse import urlparse

        from hurl.schemas.requests.site_info import SiteInfoRequest
        from tests.conftest import remove_tags

        # Generate the remote URL
        remote_url = SiteInfoRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            site="Ngahere Park Climate Station",
        ).gen_url()

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        remote_xml = remote_client.session.get(remote_url).text

        tags_to_remove = []

        # remove the tags
        remote_xml_cleaned = remove_tags(remote_xml, tags_to_remove)
        basic_response_xml_cleaned = remove_tags(basic_response_xml, tags_to_remove)

        assert remote_xml_cleaned == basic_response_xml_cleaned

    def test_collection_response_xml_fixture(
        self,
        remote_client,
        httpx_mock,
        collection_response_xml,
    ):
        """Validate the XML response from Hilltop Server."""
        from urllib.parse import urlparse

        from hurl.schemas.requests.site_info import SiteInfoRequest
        from tests.conftest import remove_tags

        # Generate the remote URL
        remote_url = SiteInfoRequest(
            base_url=remote_client.base_url,
            hts_endpoint=remote_client.hts_endpoint,
            collection="AirTemperature",
        ).gen_url()

        # Switch off httpx mock so that remote request can go through.
        httpx_mock._options.should_mock = (
            lambda request: request.url.host != urlparse(remote_client.base_url).netloc
        )

        remote_xml = remote_client.session.get(remote_url).text

        tags_to_remove = []

        # remove the tags
        remote_xml_cleaned = remove_tags(remote_xml, tags_to_remove)
        collection_response_xml_cleaned = remove_tags(collection_response_xml, tags_to_remove)

        assert remote_xml_cleaned == collection_response_xml_cleaned


class TestResponseValidation:
    def test_basic_response_xml(self, httpx_mock, basic_response_xml):
        """Validate the XML response against the SiteInfoResponse schema."""

        import pandas as pd

        from hurl.client import HilltopClient
        from hurl.schemas.requests.site_info import SiteInfoRequest
        from hurl.schemas.responses.site_info import SiteInfoResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        test_url = SiteInfoRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            site="Ngahere Park Climate Station",
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
            result = client.get_site_info(
                site="Ngahere Park Climate Station",
            )

        # Base Model
        assert isinstance(result, SiteInfoResponse)
        # Integration tests should only check structure and types, not specific organization names
        assert result.agency is not None
        assert isinstance(result.agency, str)

        df = result.to_dataframe()

        assert isinstance(df, pd.DataFrame)

        # SiteInfoResponse
        site = result.site[0]

        assert site.name == "Ngahere Park Climate Station"
        assert isinstance(site.info, dict)

        site_info = site.info

        assert site_info["Altitude"] == str(106)
        assert site_info["SecondSynonym"] == "NPK"

    def test_collection_response_xml(self, httpx_mock, collection_response_xml):
        """Validate the XML response against the SiteInfoResponse schema."""

        import pandas as pd

        from hurl.client import HilltopClient
        from hurl.schemas.requests.site_info import SiteInfoRequest
        from hurl.schemas.responses.site_info import SiteInfoResponse

        base_url = "http://example.com"
        hts_endpoint = "foo.hts"

        test_url = SiteInfoRequest(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
            collection="AirTemperature",
        ).gen_url()

        httpx_mock.add_response(
            url=test_url,
            method="GET",
            text=collection_response_xml,
        )

        with HilltopClient(
            base_url=base_url,
            hts_endpoint=hts_endpoint,
        ) as client:
            result = client.get_site_info(
                collection="AirTemperature",
            )

        # Base Model
        assert isinstance(result, SiteInfoResponse)
        # Integration tests should only check structure and types, not specific organization names
        assert result.agency is not None
        assert isinstance(result.agency, str)

        df = result.to_dataframe()
        assert isinstance(df, pd.DataFrame)

        assert len(result.site) > 1

        # SiteInfoResponse
        site = result.site[0]

        assert site.name == "Air Quality at Taihape"
        assert isinstance(site.info, dict)

        site_info = site.info

        assert site_info["Altitude"] == str(433)
        assert site_info["SecondSynonym"] == "TAQ"
