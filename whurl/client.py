"""Hilltop Client Module.

This module provides synchronous and asynchronous client classes for
interacting with Hilltop Server APIs. The clients handle request validation,
response parsing, and proper resource management.
"""

import asyncio
import os
from typing import Optional

import certifi
import httpx
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
    """A client for interacting with Hilltop Server.

    This client provides methods for making requests to Hilltop Server APIs,
    including status checks, site listings, measurement data retrieval, and
    more. It handles request validation, response parsing, and proper resource
    management.

    Parameters
    ----------
    base_url : str, optional
        Base URL for the Hilltop server. If not provided, uses
        HILLTOP_BASE_URL environment variable.
    hts_endpoint : str, optional
        HTS endpoint path (e.g., 'data.hts'). If not provided, uses
        HILLTOP_HTS_ENDPOINT environment variable.
    timeout : int, default 60
        Request timeout in seconds.
    max_connections : int, default 10
        Maximum number of connections in the connection pool.
    max_keepalive_connections : int, default 5
        Maximum number of keep-alive connections.
    http2 : bool, default False
        Whether to enable HTTP/2 support.
    verify_ssl : bool, default False
        Whether to verify SSL certificates.

    Raises
    ------
    HilltopConfigError
        If required configuration (base_url or hts_endpoint) is not provided.

    Examples
    --------
    >>> with HilltopClient() as client:
    ...     status = client.get_status()
    ...     sites = client.get_site_list()
    """

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
                max_keepalive_connections=max_keepalive_connections,
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
        """Validate HTTP response and raise HilltopResponseError if unsuccessful.

        Parameters
        ----------
        response : httpx.Response
            HTTP response object to validate.

        Raises
        ------
        HilltopResponseError
            If the response status code indicates an error.
        """
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
        """Fetch the collection list from Hilltop Server.

        Parameters
        ----------
        **kwargs
            Additional request parameters passed to CollectionListRequest.

        Returns
        -------
        CollectionListResponse
            Parsed response containing collection information.

        Raises
        ------
        HilltopResponseError
            If the HTTP request fails.
        HilltopParseError
            If the XML response cannot be parsed.
        """
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
        """Fetch measurement data from Hilltop Server.

        Parameters
        ----------
        **kwargs
            Request parameters passed to GetDataRequest. Common parameters
            include site, measurement, from_datetime, to_datetime, interval,
            method, and format.

        Returns
        -------
        GetDataResponse
            Parsed response containing measurement data with optional
            pandas DataFrame.

        Raises
        ------
        HilltopResponseError
            If the HTTP request fails.
        HilltopParseError
            If the XML response cannot be parsed.
        """
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
        """Fetch the measurement list from Hilltop Server.

        Parameters
        ----------
        **kwargs
            Additional request parameters passed to MeasurementListRequest.
            Common parameters include site and collection.

        Returns
        -------
        MeasurementListResponse
            Parsed response containing available measurements for sites.

        Raises
        ------
        HilltopResponseError
            If the HTTP request fails.
        HilltopParseError
            If the XML response cannot be parsed.
        """
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
        """Fetch detailed information about a specific site from Hilltop Server.

        Parameters
        ----------
        **kwargs
            Additional request parameters passed to SiteInfoRequest.
            The 'site' parameter is typically required.

        Returns
        -------
        SiteInfoResponse
            Parsed response containing detailed site information including
            location, parameters, and metadata.

        Raises
        ------
        HilltopResponseError
            If the HTTP request fails.
        HilltopParseError
            If the XML response cannot be parsed.
        """
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
        """Fetch the site list from Hilltop Server.

        Parameters
        ----------
        **kwargs
            Additional request parameters passed to SiteListRequest. Common
            parameters include location, bounding_box, measurement, and
            collection.

        Returns
        -------
        SiteListResponse
            Parsed response containing list of available sites with their
            basic information.

        Raises
        ------
        HilltopResponseError
            If the HTTP request fails.
        HilltopParseError
            If the XML response cannot be parsed.
        """
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
        """Fetch the server status from Hilltop Server.

        Parameters
        ----------
        **kwargs
            Additional request parameters passed to StatusRequest.

        Returns
        -------
        StatusResponse
            Parsed response containing server status information including
            version, data files, and system information.

        Raises
        ------
        HilltopResponseError
            If the HTTP request fails.
        HilltopParseError
            If the XML response cannot be parsed.
        """
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
        """Fetch the available time range for measurements from Hilltop Server.

        Parameters
        ----------
        **kwargs
            Additional request parameters passed to TimeRangeRequest.
            Common parameters include site and measurement.

        Returns
        -------
        TimeRangeResponse
            Parsed response containing the earliest and latest available
            data timestamps for the specified measurements.

        Raises
        ------
        HilltopResponseError
            If the HTTP request fails.
        HilltopParseError
            If the XML response cannot be parsed.
        """
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
        """Close the HTTP session and clean up resources."""
        self.session.close()

    def __enter__(self):
        """Enter the runtime context for use with 'with' statement.

        Returns
        -------
        HilltopClient
            The client instance for method chaining.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the runtime context and clean up resources.

        Parameters
        ----------
        exc_type : type, optional
            Exception type if an exception occurred.
        exc_value : Exception, optional
            Exception instance if an exception occurred.
        traceback : traceback, optional
            Traceback object if an exception occurred.
        """
        self.close()


class AsyncHilltopClient:
    """An asynchronous client for interacting with Hilltop Server.

    This async client provides methods for making concurrent requests to
    Hilltop Server APIs. It supports the same operations as HilltopClient
    but with async/await syntax for improved performance in concurrent
    applications.

    Parameters
    ----------
    base_url : str, optional
        Base URL for the Hilltop server. If not provided, uses
        HILLTOP_BASE_URL environment variable.
    hts_endpoint : str, optional
        HTS endpoint path (e.g., 'data.hts'). If not provided, uses
        HILLTOP_HTS_ENDPOINT environment variable.
    timeout : int, default 60
        Request timeout in seconds.
    max_connections : int, default 10
        Maximum number of connections in the connection pool.
    max_keepalive_connections : int, default 5
        Maximum number of keep-alive connections.
    http2 : bool, default False
        Whether to enable HTTP/2 support.
    verify_ssl : bool, default False
        Whether to verify SSL certificates.

    Raises
    ------
    HilltopConfigError
        If required configuration (base_url or hts_endpoint) is not provided.

    Examples
    --------
    >>> async with AsyncHilltopClient() as client:
    ...     status = await client.get_status()
    ...     sites = await client.get_site_list()
    """

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
                max_keepalive_connections=max_keepalive_connections,
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
        """Validate HTTP response and raise HilltopResponseError if unsuccessful.

        Parameters
        ----------
        response : httpx.Response
            HTTP response object to validate.

        Raises
        ------
        HilltopResponseError
            If the response status code indicates an error.
        """
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
        """Fetch the collection list from Hilltop Server asynchronously.

        Parameters
        ----------
        **kwargs
            Additional request parameters passed to CollectionListRequest.

        Returns
        -------
        CollectionListResponse
            Parsed response containing collection information.

        Raises
        ------
        HilltopResponseError
            If the HTTP request fails.
        HilltopParseError
            If the XML response cannot be parsed.
        """
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
        """Fetch measurement data from Hilltop Server asynchronously.

        Parameters
        ----------
        **kwargs
            Request parameters passed to GetDataRequest. Common parameters
            include site, measurement, from_datetime, to_datetime, interval,
            method, and format.

        Returns
        -------
        GetDataResponse
            Parsed response containing measurement data with optional
            pandas DataFrame.

        Raises
        ------
        HilltopResponseError
            If the HTTP request fails.
        HilltopParseError
            If the XML response cannot be parsed.
        """
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
        """Fetch the measurement list from Hilltop Server asynchronously.

        Parameters
        ----------
        **kwargs
            Additional request parameters passed to MeasurementListRequest.
            Common parameters include site and collection.

        Returns
        -------
        MeasurementListResponse
            Parsed response containing available measurements for sites.

        Raises
        ------
        HilltopResponseError
            If the HTTP request fails.
        HilltopParseError
            If the XML response cannot be parsed.
        """
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
        """Fetch detailed information about a site from Hilltop Server asynchronously.

        Parameters
        ----------
        **kwargs
            Additional request parameters passed to SiteInfoRequest.
            The 'site' parameter is typically required.

        Returns
        -------
        SiteInfoResponse
            Parsed response containing detailed site information including
            location, parameters, and metadata.

        Raises
        ------
        HilltopResponseError
            If the HTTP request fails.
        HilltopParseError
            If the XML response cannot be parsed.
        """
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
        """Fetch the site list from Hilltop Server asynchronously.

        Parameters
        ----------
        **kwargs
            Additional request parameters passed to SiteListRequest. Common
            parameters include location, bounding_box, measurement, and
            collection.

        Returns
        -------
        SiteListResponse
            Parsed response containing list of available sites with their
            basic information.

        Raises
        ------
        HilltopResponseError
            If the HTTP request fails.
        HilltopParseError
            If the XML response cannot be parsed.
        """
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
        """Fetch the server status from Hilltop Server asynchronously.

        Parameters
        ----------
        **kwargs
            Additional request parameters passed to StatusRequest.

        Returns
        -------
        StatusResponse
            Parsed response containing server status information including
            version, data files, and system information.

        Raises
        ------
        HilltopResponseError
            If the HTTP request fails.
        HilltopParseError
            If the XML response cannot be parsed.
        """
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
        """Fetch time range for measurements from Hilltop Server asynchronously.

        Parameters
        ----------
        **kwargs
            Additional request parameters passed to TimeRangeRequest.
            Common parameters include site and measurement.

        Returns
        -------
        TimeRangeResponse
            Parsed response containing the earliest and latest available
            data timestamps for the specified measurements.

        Raises
        ------
        HilltopResponseError
            If the HTTP request fails.
        HilltopParseError
            If the XML response cannot be parsed.
        """
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
        """Close the HTTP session and clean up resources asynchronously."""
        await self.session.aclose()

    async def __aenter__(self):
        """Enter the async runtime context for use with 'async with' statement.

        Returns
        -------
        AsyncHilltopClient
            The client instance for method chaining.
        """
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Exit the async runtime context and clean up resources.

        Parameters
        ----------
        exc_type : type, optional
            Exception type if an exception occurred.
        exc_value : Exception, optional
            Exception instance if an exception occurred.
        traceback : traceback, optional
            Traceback object if an exception occurred.
        """
        await self.close()
