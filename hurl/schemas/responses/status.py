"""Hilltop Status response schema."""

from __future__ import annotations

import xmltodict
from pydantic import BaseModel, Field, field_validator


class StatusResponse(BaseModel):
    """Represents the status of a Hilltop server."""

    class DataFile(BaseModel):
        """Represents a Hilltop data file."""

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

    @field_validator("data_files", mode="before")
    def validate_data_files(cls, value) -> list["StatusResponse.DataFile"]:
        """Ensure data_files is a list of DataFile objects."""
        if value is None:
            return []
        if isinstance(value, dict):
            return [cls.DataFile(**value)]
        return [cls.DataFile(**item) for item in value]

    def to_dict(self):
        """Convert the model to a dictionary."""
        return self.model_dump(exclude_unset=True, by_alias=True)

    @classmethod
    def from_xml(cls, xml_str: str) -> "StatusResponse":
        """Parse the XML string and return a StatusReponse object."""
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
