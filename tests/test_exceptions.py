"""Errors must say which request caused them. Among other things.

Background
----------
When a read fails, the first question is always "what did we actually as
for?". Until now only the HTTP-status failure path answered it. A server
error document or an unparseable body raised an exception with no URL, so a
caller had to rebuild the request by hand to paste it into a browser.

The rule these tests pin down:

*   Every HilltopError raised while reading a response carries ``.url`` set to
    the request URL, and the URL is in the message.
*   The URL appears in the message exactly once (the HTTP-status path already
    attached one; it must not be doubled).
*   A garbage body is a HilltopParseError, not a raw ExpatError leaking from 
    xmltodict.

Also covered here because it sits on the same code path:

*   A ``<Hilltop><Error>`` document used to hit a KeyError (the code looked up
    ``response['Error']`` instead of ``data['Error']``).
*   HilltopResponseError used to label its message "Parse error:", which is
    wrong for a server or HTTP failure.
"""

import pytest

from whurl.client import HilltopClient
from whurl.exceptions import (
    HilltopError,
    HilltopParseError,
    HilltopResponseError,
)
from whurl.schemas.requests import GetDataRequest

BASE_URL = "https://example.com"
HTS = "test.hts"
SITE = "Test Site Alpha"
MEASUREMENT = "Stage"

# The document Hilltop sends when there is nothing in the requested range.
SERVER_ERROR_XML = (
    '<?xml version="1.0"?>'
    "<HilltopServer><Error>No data found for the requested range."
    "</Error></HilltopServer>"
)

# The same kind of failure, but under the <Hilltop> root.
HILLTOP_ERROR_XML = (
    '<?xml version="1.0"?>'
    "<Hilltop><Error>Something went wrong on the server.</Error></Hilltop>"
)


@pytest.fixture
def client():
    with HilltopClient(base_url=BASE_URL, hts_endpoint=HTS) as c:
        yield c


def expected_get_data_url() -> str:
    """The URL the client should report for the get_data calls below."""
    return GetDataRequest(
        base_url=BASE_URL,
        hts_endpoint=HTS,
        site=SITE,
        measurement=MEASUREMENT,
    ).gen_url()


def call_get_data(client):
    return client.get_data(site=SITE, measurement=MEASUREMENT)


@pytest.mark.unit
class TestRequestUrlOnErrors:
    def test_server_error_document_carries_the_url(self, client, httpx_mock):
        httpx_mock.add_response(text=SERVER_ERROR_XML)

        with pytest.raises(HilltopResponseError) as caught:
            call_get_data(client)

        assert caught.value.url == expected_get_data_url()

    def test_url_is_in_the_message(self, client, httpx_mock):
        httpx_mock.add_response(text=SERVER_ERROR_XML)

        with pytest.raises(HilltopResponseError) as caught:
            call_get_data(client)

        assert expected_get_data_url() in str(caught.value)

    def test_url_appears_exactly_once_in_the_message(self, client, httpx_mock):
        httpx_mock.add_response(text=SERVER_ERROR_XML)

        with pytest.raises(HilltopResponseError) as caught:
            call_get_data(client)

        assert str(caught.value).count(expected_get_data_url()) == 1
            
    def test_http_status_failure_still_has_exactly_one_url(
        self,
        client,
        httpx_mock
    ):
        # This path already attached a URL before; adding the new wrapper
        # must not append a second copy.
        httpx_mock.add_response(status_code=500, text="boom")

        with pytest.raises(HilltopResponseError) as caught:
            call_get_data(client)

        assert caught.value.url is not None
        assert str(caught.value).count("Site=") == 1

    def test_unexpected_xml_is_a_parse_error_with_the_url(
        self, client, httpx_mock
    ):
        httpx_mock.add_response(text="<Something><Else/></Something>")

        with pytest.raises(HilltopParseError) as caught:
            call_get_data(client)

        assert caught.value.url == expected_get_data_url()

    def test_garbage_body_is_a_parse_error_not_an_expat_error(
        self, client, httpx_mock
    ):
        httpx_mock.add_response(text="this is not xml at all")

        with pytest.raises(HilltopParseError) as caught:
            call_get_data(client)

        assert caught.value.url == expected_get_data_url()
        assert caught.value.raw_response == "this is not xml at all"

    def test_every_failure_is_a_hilltop_error(self, client, httpx_mock):
        # One except clause in the caller should be enough.
        httpx_mock.add_response(text="this is not xml at all")

        with pytest.raises(HilltopError):
            call_get_data(client)

    def test_other_client_methods_get_the_url_too(self, client, httpx_mock):
        httpx_mock.add_response(text="this is not xml at all")
        
        with pytest.raises(HilltopParseError) as caught:
            client.get_site_info(site=SITE)

        assert caught.value.url is not None
        assert "SiteInfo" in caught.value.url


@pytest.mark.unit
class TestHilltopRootedError:
    def test_hilltop_error_document_is_a_response_error(
        self, client, httpx_mock
    ):
        # Used to raise KeyError: 'Error'.
        httpx_mock.add_response(text=HILLTOP_ERROR_XML)

        with pytest.raises(HilltopResponseError) as caught:
            call_get_data(client)

        assert "Something went wrong on the server." in str(caught.value)
        assert caught.value.url == expected_get_data_url()


@pytest.mark.unit
class TestResponseErrorWording:
    def test_response_error_is_not_labelled_a_parse_error(
        self, client, httpx_mock
    ):
        httpx_mock.add_response(text=SERVER_ERROR_XML)

        with pytest.raises(HilltopResponseError) as caught:
            call_get_data(client)

        assert not str(caught.value).startswith("Parse error")

    def test_parse_error_keeps_its_own_wording(self, client, httpx_mock):
        httpx_mock.add_response(text="this is not xml at all")

        with pytest.raises(HilltopParseError) as caught:
            call_get_data(client)

        assert "Parse error" in str(caught.value)
