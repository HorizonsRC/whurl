"""Hilltop Client Module."""

import asyncio
import os
from typing import Optional

import httpx
import certifi

from dotenv import load_dotenv
from pydantic import BaseModel

from whurl.exceptions import (HilltopConfigError, HilltopParseError,
                             HilltopResponseError)
from whurl.schemas.requests import (CollectionListRequest, GetDataRequest,
                                   MeasurementListRequest, SiteInfoRequest,
                                   SiteListRequest, StatusRequest,
                                   TimeRangeRequest)
from whurl.schemas.responses import (CollectionListResponse, GetDataResponse,
                                    MeasurementListResponse, SiteInfoResponse,
                                    SiteListResponse, StatusResponse,
                                    TimeRangeResponse)

load_dotenv()


class HilltopClient:
    """A client for interacting with Hilltop Server."""

    def __init__(
        self,
        base_url: str | None = None,
        hts_endpoint: str | None = None,
        timeout: int = 60,
        max_connections: int = 10,
        max_keepalive_connections: int = 5,
        http2: bool = False,
        verify_ssl: bool = False,  # Keep as False for backward compatibility
    ):
        self.base_url = base_url or os.getenv("HILLTOP_BASE_URL")
        self.hts_endpoint = hts_endpoint or os.getenv("HILLTOP_HTS_ENDPOINT")
        self.timeout = timeout
        self.max_connections = max_connections
        self.max_keepalive_connections = max_keepalive_connections
        self.http2 = http2
        self.verify_ssl = verify_ssl
        
        # Create httpx session with configurable options
        self.session = httpx.Client(
            timeout=httpx.Timeout(timeout=timeout),
            limits=httpx.Limits(
                max_connections=max_connections,
                max_keepalive_connections=max_keepalive_connections
            ),
            http2=http2,
            verify=verify_ssl,
            follow_redirects=True,
        )

        if not self.base_url:
            raise HilltopConfigError(
                "Base URL must be provided or set in environment variables."
            )

        if not self.hts_endpoint:
            raise HilltopConfigError(
                "Hilltop HTS endpoint must be provided or set in environment variables."
            )

    def _validate_response(self, response: httpx.Response) -> None:
        """Raise HilltopResponseError if the response is not successful."""
        print(f"Response status code: {response.status_code}")
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HilltopResponseError(
                f"HTTP error occurred: {e.response.status_code} - {e.response.text}",
                url=str(e.request.url),
                raw_response=e.response.text,
            ) from e

    def get_collection_list(self, **kwargs) -> CollectionListResponse:
        """Fetch the collection list from Hilltop Server."""
        request = CollectionListRequest(
            base_url=self.base_url,
            hts_endpoint=self.hts_endpoint,
            **kwargs,
        )
        response = self.session.get(request.gen_url())
        self._validate_response(response)
        result = CollectionListResponse.from_xml(response.text)
        result.request = request
        return result

    def get_data(self, **kwargs) -> GetDataResponse:
        """Fetch data from Hilltop Server."""
        request = GetDataRequest(
            base_url=self.base_url,
            hts_endpoint=self.hts_endpoint,
            **kwargs,
        )
        response = self.session.get(request.gen_url())
        self._validate_response(response)
        result = GetDataResponse.from_xml(response.text)
        result.request = request
        return result

    def get_measurement_list(self, **kwargs) -> MeasurementListResponse:
        """Fetch the measurement list from Hilltop Server."""
        request = MeasurementListRequest(
            base_url=self.base_url,
            hts_endpoint=self.hts_endpoint,
            **kwargs,
        )
        print(request.gen_url())
        response = self.session.get(request.gen_url())
        self._validate_response(response)
        result = MeasurementListResponse.from_xml(response.text)
        result.request = request
        return result

    def get_site_info(self, **kwargs) -> SiteInfoResponse:
        """Fetch the site list from Hilltop Server."""
        request = SiteInfoRequest(
            base_url=self.base_url,
            hts_endpoint=self.hts_endpoint,
            **kwargs,
        )
        response = self.session.get(request.gen_url())
        self._validate_response(response)
        result = SiteInfoResponse.from_xml(response.text)
        result.request = request
        return result

    def get_site_list(self, **kwargs) -> SiteListResponse:
        """Fetch the site list from Hilltop Server."""
        request = SiteListRequest(
            base_url=self.base_url,
            hts_endpoint=self.hts_endpoint,
            **kwargs,
        )
        response = self.session.get(request.gen_url())
        self._validate_response(response)
        result = SiteListResponse.from_xml(response.text)
        result.request = request
        return result

    def get_status(self, **kwargs) -> StatusResponse:
        """Fetch the status from Hilltop Server."""
        request = StatusRequest(
            base_url=self.base_url,
            hts_endpoint=self.hts_endpoint,
            **kwargs,
        )
        print(request.gen_url())
        response = self.session.get(request.gen_url())
        self._validate_response(response)
        result = StatusResponse.from_xml(response.text)
        result.request = request
        return result

    def get_time_range(self, **kwargs) -> TimeRangeResponse:
        """Fetch the TimeRange from Hilltop Server."""
        request = TimeRangeRequest(
            base_url=self.base_url,
            hts_endpoint=self.hts_endpoint,
            **kwargs,
        )
        response = self.session.get(request.gen_url())
        self._validate_response(response)
        result = TimeRangeResponse.from_xml(response.text)
        result.request = request
        return result

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the runtime context related to this object."""
        self.close()


class AsyncHilltopClient:
    """An async client for interacting with Hilltop Server."""

    def __init__(
        self,
        base_url: str | None = None,
        hts_endpoint: str | None = None,
        timeout: int = 60,
        max_connections: int = 10,
        max_keepalive_connections: int = 5,
        http2: bool = False,
        verify_ssl: bool = False,
    ):
        self.base_url = base_url or os.getenv("HILLTOP_BASE_URL")
        self.hts_endpoint = hts_endpoint or os.getenv("HILLTOP_HTS_ENDPOINT")
        self.timeout = timeout
        self.max_connections = max_connections
        self.max_keepalive_connections = max_keepalive_connections
        self.http2 = http2
        self.verify_ssl = verify_ssl
        
        # Create async httpx session
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout=timeout),
            limits=httpx.Limits(
                max_connections=max_connections,
                max_keepalive_connections=max_keepalive_connections
            ),
            http2=http2,
            verify=verify_ssl,
            follow_redirects=True,
        )

        if not self.base_url:
            raise HilltopConfigError(
                "Base URL must be provided or set in environment variables."
            )

        if not self.hts_endpoint:
            raise HilltopConfigError(
                "Hilltop HTS endpoint must be provided or set in environment variables."
            )

    async def _validate_response(self, response: httpx.Response) -> None:
        """Raise HilltopResponseError if the response is not successful."""
        print(f"Response status code: {response.status_code}")
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HilltopResponseError(
                f"HTTP error occurred: {e.response.status_code} - {e.response.text}",
                url=str(e.request.url),
                raw_response=e.response.text,
            ) from e

    async def get_collection_list(self, **kwargs) -> CollectionListResponse:
        """Fetch the collection list from Hilltop Server."""
        request = CollectionListRequest(
            base_url=self.base_url,
            hts_endpoint=self.hts_endpoint,
            **kwargs,
        )
        response = await self.session.get(request.gen_url())
        await self._validate_response(response)
        result = CollectionListResponse.from_xml(response.text)
        result.request = request
        return result

    async def get_data(self, **kwargs) -> GetDataResponse:
        """Fetch data from Hilltop Server."""
        request = GetDataRequest(
            base_url=self.base_url,
            hts_endpoint=self.hts_endpoint,
            **kwargs,
        )
        response = await self.session.get(request.gen_url())
        await self._validate_response(response)
        result = GetDataResponse.from_xml(response.text)
        result.request = request
        return result

    async def get_measurement_list(self, **kwargs) -> MeasurementListResponse:
        """Fetch the measurement list from Hilltop Server."""
        request = MeasurementListRequest(
            base_url=self.base_url,
            hts_endpoint=self.hts_endpoint,
            **kwargs,
        )
        print(request.gen_url())
        response = await self.session.get(request.gen_url())
        await self._validate_response(response)
        result = MeasurementListResponse.from_xml(response.text)
        result.request = request
        return result

    async def get_site_info(self, **kwargs) -> SiteInfoResponse:
        """Fetch the site info from Hilltop Server."""
        request = SiteInfoRequest(
            base_url=self.base_url,
            hts_endpoint=self.hts_endpoint,
            **kwargs,
        )
        response = await self.session.get(request.gen_url())
        await self._validate_response(response)
        result = SiteInfoResponse.from_xml(response.text)
        result.request = request
        return result

    async def get_site_list(self, **kwargs) -> SiteListResponse:
        """Fetch the site list from Hilltop Server."""
        request = SiteListRequest(
            base_url=self.base_url,
            hts_endpoint=self.hts_endpoint,
            **kwargs,
        )
        response = await self.session.get(request.gen_url())
        await self._validate_response(response)
        result = SiteListResponse.from_xml(response.text)
        result.request = request
        return result

    async def get_status(self, **kwargs) -> StatusResponse:
        """Fetch the status from Hilltop Server."""
        request = StatusRequest(
            base_url=self.base_url,
            hts_endpoint=self.hts_endpoint,
            **kwargs,
        )
        print(request.gen_url())
        response = await self.session.get(request.gen_url())
        await self._validate_response(response)
        result = StatusResponse.from_xml(response.text)
        result.request = request
        return result

    async def get_time_range(self, **kwargs) -> TimeRangeResponse:
        """Fetch the TimeRange from Hilltop Server."""
        request = TimeRangeRequest(
            base_url=self.base_url,
            hts_endpoint=self.hts_endpoint,
            **kwargs,
        )
        response = await self.session.get(request.gen_url())
        await self._validate_response(response)
        result = TimeRangeResponse.from_xml(response.text)
        result.request = request
        return result

    async def close(self):
        """Close the HTTP session."""
        await self.session.aclose()

    async def __aenter__(self):
        """Enter the async runtime context related to this object."""
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Exit the async runtime context related to this object."""
        await self.close()
