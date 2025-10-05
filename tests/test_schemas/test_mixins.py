"""Tests for ModelReprMixin functionality."""

from typing import ClassVar, Set

import pytest
import yaml
from pydantic import BaseModel, Field

from whurl.schemas.mixins import ModelReprMixin
from whurl.schemas.requests.get_data import GetDataRequest
from whurl.schemas.responses.get_data import GetDataResponse


def create_mocked_fixtures(filename: str):
    """Factory to create mocked fixtures."""

    @pytest.fixture
    def fixture_func():
        """Load test XML once per test session."""
        from pathlib import Path

        path = (
            Path(__file__).parent.parent / "mocked_data" / "get_data" / filename
        )
        raw_xml = path.read_text(encoding="utf-8")
        return raw_xml

    return fixture_func


basic_response_xml_mocked = create_mocked_fixtures("basic_response.xml")


class TestModelReprMixin:
    """Test the ModelReprMixin functionality."""

    def test_header_appears_in_repr(self):
        """Test that the model name appears as a header in the repr."""
        request = GetDataRequest(
            base_url="https://example.com", hts_endpoint="test.hts", site="Test Site"
        )

        repr_str = str(request)
        assert repr_str.startswith("GetDataRequest:")
        assert "base_url: https://example.com" in repr_str
        assert "site: Test Site" in repr_str

    def test_yaml_validity(self):
        """Test that the output is valid YAML."""
        request = GetDataRequest(
            base_url="https://example.com",
            hts_endpoint="test.hts",
            site="Test Site",
            measurement="Flow",
        )

        repr_str = str(request)

        # Should be parseable as YAML
        parsed = yaml.safe_load(repr_str)
        assert isinstance(parsed, dict)
        assert "GetDataRequest" in parsed

        # Check that important fields are present
        request_data = parsed["GetDataRequest"]
        assert request_data["base_url"] == "https://example.com"
        assert request_data["site"] == "Test Site"
        assert request_data["measurement"] == "Flow"

    def test_none_values_excluded(self):
        """Test that None values are excluded from the output."""
        request = GetDataRequest(
            base_url="https://example.com",
            hts_endpoint="test.hts",
            site="Test Site",
            measurement=None,  # This should be excluded
            from_datetime="2023-01-01T00:00:00",
        )

        repr_str = str(request)
        assert "measurement:" not in repr_str
        assert "from_datetime: '2023-01-01T00:00:00'" in repr_str

    def test_nested_models_recursive(self, basic_response_xml_mocked):
        """Test that nested models are recursively formatted."""
        # Create a response with nested models

        response = GetDataResponse.from_xml(basic_response_xml_mocked)
        repr_str = str(response)

        # Should contain nested structure with proper indentation
        assert "GetDataResponse:" in repr_str
        assert "measurement:" in repr_str
        assert "data_source:" in repr_str
        assert "item_info:" in repr_str
        assert "item_name: Stage" in repr_str

    def test_repr_include_unset_functionality(self):
        """Test the repr_include_unset functionality."""

        class TestModel(ModelReprMixin, BaseModel):
            """Test model with repr_include_unset defined."""

            repr_include_unset: ClassVar[Set[str]] = {"important_field"}

            name: str
            optional_field: str = None
            important_field: str = None

        model = TestModel(name="test")
        repr_str = str(model)

        # optional_field should be excluded (None and not in repr_include_unset)
        assert "optional_field:" not in repr_str

        # important_field should be included (in repr_include_unset)
        assert "important_field: null" in repr_str or "important_field:" in repr_str

    def test_pandas_dataframe_handling(self):
        """Test that pandas DataFrames are handled gracefully."""
        sample_data = {
            "Agency": "Test Agency",
            "Measurement": [
                {
                    "@SiteName": "Test Site",
                    "DataSource": {
                        "@Name": "Test DataSource",
                        "@NumItems": "1",
                        "TSType": "StdSeries",
                        "DataType": "Flow",
                        "Interpolation": "Discrete",
                    },
                    "Data": {
                        "@DateFormat": "Calendar",
                        "@NumItems": "1",
                        "E": [{"T": "2023-01-01T00:00:00", "I1": "10.5"}],
                    },
                }
            ],
        }

        response = GetDataResponse(**sample_data)
        repr_str = str(response)

        # Should contain DataFrame summary, not raw data
        assert "timeseries: '<DataFrame:" in repr_str
        assert "rows × " in repr_str
        assert "columns>'" in repr_str
