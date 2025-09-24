"""Mixins for Pydantic models in whurl.schemas.

This module provides mixin classes that extend Pydantic models with
additional functionality for consistent string representations and
YAML-formatted output.
"""

from typing import Any, Dict, Set

import yaml
from pydantic import BaseModel


class ModelReprMixin:
    """Mixin providing YAML-style __repr__ and __str__ methods for Pydantic models.

    This mixin provides pretty-printed, recursive output for Pydantic models using
    PyYAML. String representations begin with a header indicating the model type and
    show all set values with proper indentation and line breaks. Unset/None parameters
    are excluded unless specified in repr_include_unset.

    To include specific fields even when they are None/unset, define repr_include_unset
    as a ClassVar in your model:

    from typing import ClassVar, Set

    class MyModel(ModelReprMixin, BaseModel):
        repr_include_unset: ClassVar[Set[str]] = {"important_field"}

        important_field: str = None
        other_field: str = None
    """

    def _get_repr_include_unset(self) -> Set[str]:
        """Get the set of fields that should always be included in repr.

        Returns
        -------
        Set[str]
            Set of field names that should be included even when unset/None.
        """
        # Try to get repr_include_unset from the class
        return getattr(self.__class__, "repr_include_unset", set())

    def _to_yaml_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary suitable for YAML output.

        Returns
        -------
            Dictionary representation excluding unset values unless in
            repr_include_unset.
        """
        # Get all field values, excluding unset ones
        data = self.model_dump(exclude_unset=True)

        # Add any fields that should always be included
        include_unset = self._get_repr_include_unset()
        if include_unset:
            all_data = self.model_dump(exclude_unset=False)
            for field in include_unset:
                if field in all_data:
                    data[field] = all_data[field]

        # Remove None values unless they're explicitly required
        filtered_data = {}
        for key, value in data.items():
            if value is None and key not in include_unset:
                continue  # Skip None values
            filtered_data[key] = value

        return self._process_nested_models(filtered_data)

    def _process_nested_models(self, data: Any) -> Any:
        """Recursively process nested models and lists for YAML representation.

        This method handles conversion of complex data types including nested
        Pydantic models, pandas DataFrames, and other special types into
        formats suitable for YAML display.

        Parameters
        ----------
        data : Any
            Data to process (could be dict, list, BaseModel, etc.)

        Returns
        -------
        Any
            Processed data with nested models converted appropriately.
        """
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                result[key] = self._process_nested_models(value)
            return result
        elif isinstance(data, list):
            return [self._process_nested_models(item) for item in data]
        elif isinstance(data, BaseModel):
            # For nested models, get their yaml dict representation
            if hasattr(data, "_to_yaml_dict"):
                return data._to_yaml_dict()
            else:
                return data.model_dump(exclude_unset=True)
        else:
            # Handle special types that need formatting
            import pandas as pd

            if isinstance(data, pd.DataFrame):
                # Convert DataFrame to a more readable format
                if data.empty:
                    return "<Empty DataFrame>"
                else:
                    # Convert to a simple table representation
                    return (
                        f"<DataFrame: {data.shape[0]} rows × {data.shape[1]} columns>"
                    )
            elif isinstance(data, pd.Series):
                return f"<Series: {len(data)} values>"
            elif hasattr(data, "to_dict") and callable(data.to_dict):
                try:
                    return data.to_dict()
                except Exception:
                    return str(data)
            return data

    def _to_yaml(self) -> str:
        """Generate YAML string representation of the model.

        Returns
        -------
            YAML formatted string with model header.
        """
        class_name = self.__class__.__name__
        data = self._to_yaml_dict()

        # Create the header with the class name
        yaml_content = {class_name: data}

        # Use PyYAML to generate clean output
        yaml_str = yaml.dump(
            yaml_content,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            indent=2,
            width=80,
        )

        return yaml_str.rstrip()  # Remove trailing newline

    def __repr__(self) -> str:
        """Return YAML-style representation of the model.

        Returns
        -------
        str
            YAML-formatted string representation of the model.
        """
        return self._to_yaml()

    def __str__(self) -> str:
        """Return YAML-style string representation of the model.

        Returns
        -------
        str
            YAML-formatted string representation of the model.
        """
        return self._to_yaml()
