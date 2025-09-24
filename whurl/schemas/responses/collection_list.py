"""Contains the schema for the Hilltop CollectionList response."""

import xmltodict
from pydantic import BaseModel, Field, field_validator

from whurl.schemas.mixins import ModelReprMixin
from whurl.schemas.requests import CollectionListRequest


class CollectionListResponse(ModelReprMixin, BaseModel):
    """Top-level Hilltop CollectionList response model."""

    class Collection(ModelReprMixin, BaseModel):
        """Represents a single Hilltop collection."""

        class Item(ModelReprMixin, BaseModel):
            """Represents an item in a Hilltop collection."""

            site_name: str | None = Field(alias="SiteName")
            measurement: str | None = Field(alias="Measurement")
            filename: str | None = Field(alias="Filename", default=None)

            def to_dict(self):
                """Convert the model to a dictionary."""
                return self.model_dump(exclude_unset=True, by_alias=True)

        name: str = Field(alias="@Name")
        items: list[Item] = Field(alias="Item", default_factory=list)

        @field_validator("items", mode="before")
        def validate_items(cls, value) -> list["Item"]:
            """Ensure items is a list, even when there is only one."""
            if value is None:
                return []
            if isinstance(value, dict):
                return [cls.Item(**value)]
            return [cls.Item(**item) for item in value]

        def to_dict(self):
            """Convert the model to a dictionary."""
            return self.model_dump(exclude_unset=True, by_alias=True)

    title: str | None = Field(alias="Title", default=None)
    collections: list[Collection] = Field(alias="Collection", default_factory=list)
    request: CollectionListRequest | None = Field(default=None, exclude=True)

    def to_dict(self):
        """Convert the model to a dictionary."""
        return self.model_dump(exclude_unset=True, by_alias=True)

    @classmethod
    def from_xml(cls, xml_str: str) -> "MeasurementListResponse":
        """Parse the XML string and return a HilltopMeasurementList object."""
        response = xmltodict.parse(xml_str)

        if "HilltopProject" not in response:
            raise HilltopParseError(
                "Unexpected Hilltop XML response.", raw_response=xml_str
            )
        data = response["HilltopProject"]

        if "Collection" in data:
            if not isinstance(data["Collection"], list):
                data["Collection"] = [data["Collection"]]

        return cls(**data)
