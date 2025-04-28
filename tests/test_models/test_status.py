from hurl.client import HilltopClient
from hurl.models.status import HilltopStatus
from hurl.exceptions import HilltopResponseError
import pytest
import xmltodict
from pathlib import Path
from tests.conftest import remove_tags


@pytest.fixture
def status_response_xml(request, remote_client):
    """Fixture for HilltopStatus response XML."""
    path = Path(__file__).parent.parent / "fixture_cache" / "status" / "response.xml"

    if request.config.getoption("--update"):
        remote_url = HilltopStatus.gen_url(
            remote_client.base_url, remote_client.hts_endpoint
        )
        remote_xml = remote_client.session.get(remote_url).text

        path.write_text(remote_xml, encoding="utf-8")

    raw_xml = path.read_text(encoding="utf-8")

    return raw_xml


@pytest.fixture
def mock_hilltop_client(mocker, status_response_xml):
    """Mock HilltopClient."""
    # Mock the response
    mock_response = mocker.MagicMock()
    mock_response.text = status_response_xml
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
    def test_response_xml_fixture(self, remote_client, status_response_xml):
        """Validate the status response XML fixture."""
        from hurl.models.status import HilltopStatus

        cached_xml = status_response_xml

        remote_url = HilltopStatus.gen_url(
            remote_client.base_url, remote_client.hts_endpoint
        )
        remote_xml = remote_client.session.get(remote_url).text

        tags_to_remove = [
            "ProcessID",
            "WorkingSet",
            "OpenFor",
            "FullRefresh",
            "SoftRefresh",
        ]

        # remove the tags OpenFor, FullRefresh and SoftRefresh and their contents
        remote_xml_cleaned = remove_tags(remote_xml, tags_to_remove)
        cached_xml_cleaned = remove_tags(cached_xml, tags_to_remove)

        assert remote_xml_cleaned == cached_xml_cleaned


class TestStatus:
    def test_gen_status_url(self):
        from hurl.models.status import (
            gen_status_url,
            HilltopStatus,
        )

        correct_url = "http://example.com/foo.hts?Request=Status&Service=Hilltop"

        test_url = gen_status_url(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
        )

        assert test_url == correct_url

        test_method_gen_url = HilltopStatus.gen_url(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
        )

        assert test_method_gen_url == correct_url

    def test_from_url(self, mock_hilltop_client):
        """Test from_url method."""
        mock_client = mock_hilltop_client["client"]
        mock_session = mock_hilltop_client["session"]

        test_url = "http://example.com/foo.hts?Request=Status&Service=Hilltop"

        # 5. Test the actual method
        result = HilltopStatus.from_url(test_url, timeout=60, client=mock_client)

        # 6. Verify behavior
        mock_session.get.assert_called_once_with(test_url, timeout=60)
        assert isinstance(result, HilltopStatus)
        assert result.agency == "Horizons"
        assert result.script_name == "/boo.hts"

    def test_from_params(self, mock_hilltop_client):
        """Test from_params method."""
        mock_client = mock_hilltop_client["client"]
        mock_session = mock_hilltop_client["session"]

        result = HilltopStatus.from_params(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            timeout=60,
            client=mock_client,
        )

        test_url = (
            "http://example.com/foo.hts?Request=Status&Service=Hilltop"
        )

        mock_session.get.assert_called_once_with(
            test_url,
            timeout=60,
        )
        assert isinstance(result, HilltopStatus)
