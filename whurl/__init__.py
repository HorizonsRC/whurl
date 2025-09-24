"""WHURL - Which Hydro URL.

A Python client library for interacting with Hilltop Server APIs, providing a
clean interface for fetching environmental and scientific data from Hilltop
servers.

This package provides:
- HilltopClient: Synchronous client for Hilltop API operations
- AsyncHilltopClient: Asynchronous client for Hilltop API operations
- Pydantic-based request validation and response parsing
- Comprehensive error handling and configuration management
"""

from .client import AsyncHilltopClient, HilltopClient

__author__ = """Nic Mostert"""
__email__ = "nicolas.mostert@horizons.govt.nz"
__version__ = "0.1.0"

__all__ = ["HilltopClient", "AsyncHilltopClient"]
