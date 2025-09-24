"""Hilltop Status Request Model.

This module defines the request model for retrieving Hilltop Server status
information including version, data files, and system details.
"""

from pydantic import Field, field_validator

from whurl.exceptions import HilltopRequestError
from whurl.schemas.mixins import ModelReprMixin
from whurl.schemas.requests.base import BaseHilltopRequest


class StatusRequest(BaseHilltopRequest):
    """Request parameters for Hilltop server status information.

    This request type retrieves basic information about the Hilltop Server
    including version, process ID, data files, and system status.

    Parameters
    ----------
    request : str, default "Status"
        Fixed request type for status queries.
    """

    request: str = Field(default="Status", serialization_alias="Request")

    @field_validator("request", mode="before")
    def validate_request(cls, value):
        """Validate the request parameter is 'Status'.

        Parameters
        ----------
        value : str
            The request type to validate.

        Returns
        -------
        str
            The validated request type.

        Raises
        ------
        HilltopRequestError
            If the request type is not 'Status'.
        """
        if value != "Status":
            raise HilltopRequestError("Request must be 'Status'")
        return value
