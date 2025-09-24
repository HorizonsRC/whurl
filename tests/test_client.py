"""Test for the client module."""

import os

import pytest
from dotenv import load_dotenv


def test_hilltop_client_import():
    """Test that the Hilltop client module can be imported."""
    from whurl.client import HilltopClient  # noqa: F401


def test_async_hilltop_client_import():
    """Test that the Async Hilltop client module can be imported."""
    from whurl.client import AsyncHilltopClient  # noqa: F401


def test_hilltop_client_init():
    """Test that the HilltopClient can be instantiated."""
    from whurl.client import HilltopClient

    client = HilltopClient()
    assert client is not None
    assert isinstance(client, HilltopClient)
    assert client.base_url == os.getenv("HILLTOP_BASE_URL")
    assert client.hts_endpoint == os.getenv("HILLTOP_HTS_ENDPOINT")


def test_async_hilltop_client_init():
    """Test that the AsyncHilltopClient can be instantiated."""
    from whurl.client import AsyncHilltopClient, HilltopClient

    client = AsyncHilltopClient()
    assert client is not None
    assert isinstance(client, AsyncHilltopClient)
    assert client.base_url == os.getenv("HILLTOP_BASE_URL")
    assert client.hts_endpoint == os.getenv("HILLTOP_HTS_ENDPOINT")


def test_hilltop_client_config_error():
    """Test that the HilltopClient raises an error with invalid config."""
    import os

    import pytest

    from whurl.client import HilltopClient
    from whurl.exceptions import HilltopConfigError

    # Pretend that there are no environment variables set
    base_url = os.environ.pop("HILLTOP_BASE_URL", None)

    with pytest.raises(HilltopConfigError):
        client = HilltopClient()  # type: ignore

    # Restore environment variables
    if base_url is not None:
        os.environ["HILLTOP_BASE_URL"] = base_url

    hts_endpoint = os.environ.pop("HILLTOP_HTS_ENDPOINT", None)

    with pytest.raises(HilltopConfigError):
        client = HilltopClient()  # type: ignore

    # Restore environment variables
    if hts_endpoint is not None:
        os.environ["HILLTOP_HTS_ENDPOINT"] = hts_endpoint


def test_async_hilltop_client_config_error():
    """Test that the HilltopClient raises an error with invalid config."""
    import os

    import pytest

    from whurl.client import AsyncHilltopClient
    from whurl.exceptions import HilltopConfigError

    # Pretend that there are no environment variables set
    base_url = os.environ.pop("HILLTOP_BASE_URL", None)

    with pytest.raises(HilltopConfigError):
        client = AsyncHilltopClient()  # type: ignore

    # Restore environment variables
    if base_url is not None:
        os.environ["HILLTOP_BASE_URL"] = base_url

    hts_endpoint = os.environ.pop("HILLTOP_HTS_ENDPOINT", None)

    with pytest.raises(HilltopConfigError):
        client = AsyncHilltopClient()  # type: ignore

    # Restore environment variables
    if hts_endpoint is not None:
        os.environ["HILLTOP_HTS_ENDPOINT"] = hts_endpoint


def test_hilltop_client_validate_response():
    """Test that the HilltopClient can validate a response."""
    import httpx

    from whurl.client import HilltopClient
    from whurl.exceptions import HilltopResponseError

    client = HilltopClient(base_url="https://example.com", hts_endpoint="test.hts")
    # Mock a valid httpx response
    valid_response = httpx.Response(
        status_code=200,
        request=httpx.Request("GET", "https://example.com/test.hts"),
        content=b"<xml>valid</xml>",
    )
    # The _validate_response method should return None for a valid response
    # It just raises an error if the response is invalid
    assert client._validate_response(valid_response) is None

    # Mock an httpx.HTTPStatusError response
    invalid_response = httpx.Response(
        status_code=404,
        request=httpx.Request("GET", "https://example.com/test.hts"),
        content=b"<xml>You done goofed.</xml>",
    )
    with pytest.raises(HilltopResponseError):
        client._validate_response(invalid_response)


async def test_async_hilltop_client_validate_response():
    """Test that the AsyncHilltopClient can validate a response."""
    import httpx

    from whurl.client import AsyncHilltopClient
    from whurl.exceptions import HilltopResponseError

    client = AsyncHilltopClient(base_url="https://example.com", hts_endpoint="test.hts")
    # Mock a valid httpx response
    valid_response = httpx.Response(
        status_code=200,
        request=httpx.Request("GET", "https://example.com/test.hts"),
        content=b"<xml>valid</xml>",
    )
    # The _validate_response method should return None for a valid response
    # It just raises an error if the response is invalid
    assert await client._validate_response(valid_response) is None

    # Mock an httpx.HTTPStatusError response
    invalid_response = httpx.Response(
        status_code=404,
        request=httpx.Request("GET", "https://example.com/test.hts"),
        content=b"<xml>You done goofed.</xml>",
    )
    with pytest.raises(HilltopResponseError):
        await client._validate_response(invalid_response)
