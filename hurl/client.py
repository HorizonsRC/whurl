"""Hilltop Client Module."""

import os

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel

from hurl.exceptions import (HilltopConfigError, HilltopParseError,
                             HilltopResponseError)
from hurl.schemas.requests import (MeasurementListRequest, SiteListRequest,
                                   StatusRequest)
from hurl.schemas.responses import (MeasurementListResponse, SiteListResponse,
                                    StatusResponse)

load_dotenv()


class HilltopClient:
    """A client for interacting with Hilltop Server."""

    def __init__(
        self,
        base_url: str | None = None,
        hts_endpoint: str | None = None,
        timeout: int = 60,
    ):
        self.base_url = base_url or os.getenv("HILLTOP_BASE_URL")
        self.hts_endpoint = hts_endpoint or os.getenv("HILLTOP_HTS_ENDPOINT")
        self.timeout = timeout
        self.session = httpx.Client(
            timeout=httpx.Timeout(timeout=timeout),
            limits=httpx.Limits(max_connections=10),
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
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HilltopResponseError(
                f"HTTP error occurred: {e.response.status_code} - {e.response.text}",
                url=str(e.request.url),
                raw_response=e.response.text,
            ) from e

    def get_measurement_list(self, **kwargs) -> MeasurementListResponse:
        """Fetch the measurement list from Hilltop Server."""
        params = MeasurementListRequest(
            base_url=self.base_url,
            hts_endpoint=self.hts_endpoint,
            **kwargs,
        )
        response = self.session.get(params.gen_url())
        self._validate_response(response)
        return MeasurementListResponse.from_xml(response.text)

    def get_site_list(self, **kwargs) -> SiteListResponse:
        """Fetch the site list from Hilltop Server."""
        params = SiteListRequest(
            base_url=self.base_url,
            hts_endpoint=self.hts_endpoint,
            **kwargs,
        )
        response = self.session.get(params.gen_url())
        self._validate_response(response)
        return SiteListResponse.from_xml(response.text)

    def get_status(self, **kwargs) -> StatusResponse:
        """Fetch the status from Hilltop Server."""
        params = StatusRequest(
            base_url=self.base_url,
            hts_endpoint=self.hts_endpoint,
            **kwargs,
        )
        print(params.gen_url())
        response = self.session.get(params.gen_url())
        self._validate_response(response)
        return StatusResponse.from_xml(response.text)

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the runtime context related to this object."""
        self.close()
