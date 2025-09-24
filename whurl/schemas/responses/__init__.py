"""Response models for HilltopServer API.

This package provides Pydantic models for parsing and validating
responses from various Hilltop Server API endpoints.
"""

__author__ = """Nic Mostert"""
__email__ = "nicolas.mostert@horizons.govt.nz"
__version__ = "0.1.0"

from .collection_list import CollectionListResponse
from .get_data import GetDataResponse
from .measurement_list import MeasurementListResponse
from .site_info import SiteInfoResponse
from .site_list import SiteListResponse
from .status import StatusResponse
from .time_range import TimeRangeResponse

__all__ = [
    "MeasurementListResponse",
    "SiteInfoResponse",
    "SiteListResponse",
    "StatusResponse",
    "GetDataResponse",
    "CollectionListResponse",
    "TimeRangeResponse",
]
