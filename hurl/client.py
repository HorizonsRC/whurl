"""Hilltop Client Module."""

import os
from typing import Optional
from urllib.parse import urljoin
import httpx
from pydantic import BaseModel
from dotenv import load_dotenv

from hurl.models.measurement_list import HilltopMeasurementList
from hurl.exceptions import HilltopParseError, HilltopRequestError, HilltopConfigError, raise_for_response

load_dotenv()


class HilltopClient:
    """A client for interacting with Hilltop Server."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        hts_endpoint: Optional[str] = None,
        timeout: int = 60,
    ):
        self.base_url = base_url or os.getenv("HILLTOP_BASE_URL")
        self.hts_endpoint = hts_endpoint or os.getenv("HILLTOP_HTS_ENDPOINT")
        self.timeout = timeout
        self.session = httpx.Client(timeout=timeout)

        if not self.base_url:
            raise HilltopConfigError(
                "Base URL must be provided or set in environment variables."
            )

        if not self.hts_endpoint:
            raise HilltopConfigError(
                "Hilltop HTS endpoint must be provided or set in environment variables."
            )

    def get_measurement_list(
        self,
        site: Optional[str] = None,
        collection: Optional[str] = None,
        units: Optional[str] = None,
        target: Optional[str] = None,
    ) -> HilltopMeasurementList:
        """Fetch the measurement list from Hilltop Server."""
        url = HilltopMeasurementList.gen_url(
            self.base_url, self.hts_endpoint, site, collection, units, target
        )

        response = self.session.get(url)

        try:
            raise_for_response(response)
            return HilltopMeasurementList.from_xml(response.text)
        except ValueError as e:
            raise HilltopParseError(
                str(e), url=url, raw_response=response.text
            )

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the runtime context related to this object."""
        self.close()
