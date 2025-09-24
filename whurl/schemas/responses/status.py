"""Hilltop Status response schema.

This module defines the response models for parsing Hilltop Server status
information returned by the Status API endpoint.
"""

from __future__ import annotations

import xmltodict
from pydantic import BaseModel, Field, field_validator

from whurl.exceptions import HilltopParseError
from whurl.schemas.mixins import ModelReprMixin
from whurl.schemas.requests import StatusRequest


class StatusResponse(ModelReprMixin, BaseModel):
    """Represents the status response from a Hilltop server.

    This model contains information about the server's current state,
    including version details, data files, and system metrics.

    Attributes
    ----------
    agency : str, optional
        The agency operating the Hilltop server.
    version : str, optional
        The Hilltop server version number.
    script_name : str, optional
        The name of the server script/endpoint.
    default_file : str, optional
        The default data file being served.
    relay_url : str, optional
        URL for relayed requests, if configured.
    process_id : int, optional
        The server process identifier.
    working_set : float, optional
        Memory working set size in MB.
    data_files : list of DataFile, optional
        List of data files available on the server.
    request : StatusRequest, optional
        The original request that generated this response (excluded from output).
    """

    class DataFile(ModelReprMixin, BaseModel):
        """Represents a Hilltop data file.

        Contains information about individual data files managed by
        the Hilltop server, including usage statistics and refresh
        information.

        Attributes
        ----------
        filename : str
            The name of the data file.
        usage_count : int, optional
            Number of times the file has been accessed.
        open_for : int, optional
            Duration the file has been open (in seconds).
        full_refresh : int, optional
            Timestamp of last full refresh.
        soft_refresh : int, optional
            Timestamp of last soft refresh.
        """

        filename: str = Field(alias="Filename")
        usage_count: int | None = Field(alias="UsageCount", default=None)
        open_for: int | None = Field(alias="OpenFor", default=None)
        full_refresh: int | None = Field(alias="FullRefresh", default=None)
        soft_refresh: int | None = Field(alias="SoftRefresh", default=None)

    agency: str | None = Field(alias="Agency", default=None)
    version: str | None = Field(alias="Version", default=None)
    script_name: str | None = Field(alias="ScriptName", default=None)
    default_file: str | None = Field(alias="DefaultFile", default=None)
    relay_url: str | None = Field(alias="RelayURL", default=None)
    process_id: int | None = Field(alias="ProcessID", default=None)
    working_set: float | None = Field(alias="WorkingSet", default=None)
    data_files: list[DataFile] | None = Field(alias="DataFile", default_factory=list)
    request: StatusRequest | None = Field(default=None, exclude=True)

    @field_validator("data_files", mode="before")
    def validate_data_files(cls, value) -> list["StatusResponse.DataFile"]:
        """Ensure data_files is a list of DataFile objects.

        Handles both single DataFile dictionaries and lists of DataFile
        dictionaries from the XML parsing process.

        Parameters
        ----------
        value : dict or list or None
            The data files value from XML parsing.

        Returns
        -------
        list of DataFile
            List of DataFile model instances.
        """
        if value is None:
            return []
        if isinstance(value, dict):
            return [cls.DataFile(**value)]
        return [cls.DataFile(**item) for item in value]

    def to_dict(self):
        """Convert the model to a dictionary representation.

        Returns
        -------
        dict
            Dictionary representation of the status response with unset
            values excluded and using field aliases.
        """
        return self.model_dump(exclude_unset=True, by_alias=True)

    @classmethod
    def from_xml(cls, xml_str: str) -> "StatusResponse":
        """Parse XML string and return a StatusResponse object.

        Converts the XML response from Hilltop Server into a structured
        StatusResponse model with proper validation and type conversion.

        Parameters
        ----------
        xml_str : str
            The XML string returned by the Hilltop server.

        Returns
        -------
        StatusResponse
            Parsed and validated status response model.

        Raises
        ------
        HilltopParseError
            If the XML is invalid or missing required HilltopServer root element.
        """
        response = xmltodict.parse(xml_str)

        if "HilltopServer" not in response:
            raise HilltopParseError(
                "Invalid Hilltop server response", raw_response=response
            )

        data = response["HilltopServer"]

        if "DataFile" in data:
            # Ensure DataFile is a list
            if not isinstance(data["DataFile"], list):
                data["DataFile"] = [data["DataFile"]]

        return cls(**data)
