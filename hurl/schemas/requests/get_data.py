"""GetData request schema."""

from pydantic import Field

from hurl.schemas.requests.base import BaseHilltopRequest


class GetDataRequest(BaseHilltopRequest):
    """Request parameters for Hilltop GetData."""

    request: str = Field(default="GetData", serialization_alias="Request")
    site: str | None = Field(default=None, serialization_alias="Site")
    measurement: str | None = Field(default=None, serialization_alias="Measurement")
    from_datetime: str | None = Field(default=None, serialization_alias="From")
    to_datetime: str | None = Field(default=None, serialization_alias="To")
    time_interval: str | None = Field(default=None, serialization_alias="TimeInterval")
    alignment: str | None = Field(default=None, serialization_alias="Alignment")
    collection: str | None = Field(default=None, serialization_alias="Collection")
    method: str | None = Field(default=None, serialization_alias="Method")
    interval: str | None = Field(default=None, serialization_alias="Interval")
    gap_tolerance: str | None = Field(default=None, serialization_alias="GapTolerance")
    show_final: str | None = Field(default=None, serialization_alias="ShowFinal")
    date_only: str | None = Field(default=None, serialization_alias="DateOnly")
    send_as: str | None = Field(default=None, serialization_alias="SendAs")
    agency: str | None = Field(default=None, serialization_alias="Agency")
    format: str | None = Field(default=None, serialization_alias="Format")
    ts_type: str | None = Field(default=None, serialization_alias="TSType")
    show_quality: str | None = Field(default=None, serialization_alias="ShowQuality")
