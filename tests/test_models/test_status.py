"""Test the HilltopStatus class."""

import pytest


@pytest.fixture
def status_response_xml(request, remote_client):
    """Fixture for HilltopStatus response XML."""
    from pathlib import Path

    from hurl.models.status import HilltopStatus

    path = Path(__file__).parent.parent / "fixture_cache" / "status" / "response.xml"

    if request.config.getoption("--update"):
        remote_url = HilltopStatus.gen_url(
            remote_client.base_url, remote_client.hts_endpoint
        )
        remote_xml = remote_client.session.get(remote_url).text

        path.write_text(remote_xml, encoding="utf-8")

    raw_xml = path.read_text(encoding="utf-8")

    return raw_xml


class TestRemoteFixtures:
    @pytest.mark.remote
    @pytest.mark.update
    def test_response_xml_fixture(self, remote_client, status_response_xml):
        """Validate the status response XML fixture."""
        from hurl.models.status import HilltopStatus
        from tests.conftest import remove_tags

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


class TestParameterValidation:
    def test_gen_status_url(self):
        from hurl.models.status import HilltopStatus, gen_status_url

        correct_url = "http://example.com/foo.hts?Service=Hilltop&Request=Status"

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

    def test_parameter_validators(self):
        """Test the parameter validators."""
        from hurl.models.request_parameters import HilltopRequestParameters
        from hurl.exceptions import HilltopHTTPError

        # Test valid parameters
        params = HilltopRequestParameters(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            service="Hilltop",
            request="Status",
        )
        assert params.base_url == "http://example.com"
        assert params.hts_endpoint == "foo.hts"
        assert params.service == "Hilltop"
        assert params.request == "Status"
        # Test invalid parameters
        with pytest.raises(HilltopHTTPError):
            HilltopRequestParameters(
                base_url="Not a url",
                hts_endpoint="Not an hts file",
                service="Not Hilltop",
                request="Not a valid request",
            )


class TestResponseValidation:

    def test_from_url(self, mock_hilltop_client_factory, status_response_xml):
        """Test from_url method."""
        import os
        from dotenv import load_dotenv

        from hurl.models.status import HilltopStatus

        load_dotenv()

        # Set up the mock client
        mock_hilltop_client = mock_hilltop_client_factory(
            response_xml=status_response_xml,
            status_code=200,
        )

        mock_client = mock_hilltop_client["client"]
        mock_session = mock_hilltop_client["session"]

        test_url = "http://example.com/foo.hts?Service=Hilltop&Request=Status"

        # 5. Test the actual method
        result = HilltopStatus.from_url(test_url, timeout=60, client=mock_client)

        # 6. Verify behavior
        mock_session.get.assert_called_once_with(test_url, timeout=60)
        assert isinstance(result, HilltopStatus)
        assert result.agency == "Horizons"
        assert result.script_name == os.getenv("HILLTOP_HTS_ENDPOINT")
        assert len(result.data_files) == 1

    def test_from_params(self, mock_hilltop_client_factory, status_response_xml):
        """Test from_params method."""
        import os
        from dotenv import load_dotenv

        from hurl.models.status import HilltopStatus

        load_dotenv()

        # Set up the mock client
        mock_hilltop_client = mock_hilltop_client_factory(
            response_xml=status_response_xml,
            status_code=200,
        )
        mock_client = mock_hilltop_client["client"]
        mock_session = mock_hilltop_client["session"]

        result = HilltopStatus.from_params(
            base_url="http://example.com",
            hts_endpoint="foo.hts",
            timeout=60,
            client=mock_client,
        )

        test_url = "http://example.com/foo.hts?Service=Hilltop&Request=Status"

        mock_session.get.assert_called_once_with(
            test_url,
            timeout=60,
        )
        assert isinstance(result, HilltopStatus)
        assert result.agency == "Horizons"
        assert result.script_name == os.getenv("HILLTOP_HTS_ENDPOINT")
        assert len(result.data_files) == 1

    def test_to_dict(self, status_response_xml):
        """Test to_dict method."""
        import xmltodict
        from hurl.models.status import HilltopStatus

        site_list = HilltopStatus.from_xml(status_response_xml)
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
