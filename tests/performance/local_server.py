"""Local FastAPI test server for performance testing.

This module provides a FastAPI-based test server that serves fixture data
from the cache with configurable delays and error simulation for testing
httpx performance features like connection pooling, keep-alive, HTTP/2, etc.
"""

import asyncio
import os
import time
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import PlainTextResponse


class LocalTestServer:
    """FastAPI-based local test server for performance testing."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8000,
        mocked_data_path: Optional[Path] = None,
        default_delay: float = 0.0,
        error_rate: float = 0.0,
    ):
        """Initialize the local test server.

        Args:
        ----
            host: Host to bind to (default: 127.0.0.1)
            port: Port to bind to (default: 8000)
            mocked_data_path: Path to fixture cache directory
            default_delay: Default artificial delay in seconds
            error_rate: Rate of errors to simulate (0.0-1.0)
        """
        self.host = host
        self.port = port
        self.default_delay = default_delay
        self.error_rate = error_rate

        # Set fixture cache path
        if mocked_data_path is None:
            self.mocked_data_path = Path(__file__).parent.parent / "mocked_data"
        else:
            self.mocked_data_path = mocked_data_path

        self.app = FastAPI(
            title="WHURL Performance Test Server",
            description="Local test server for httpx performance testing",
            version="1.0.0",
        )

        # Hardcoded fixture mapping (can be extended to config-based later)
        self.fixture_mapping = {
            # StatusRequest endpoint
            "/foo.hts": {
                "Service=Hilltop&Request=Status": "status/response.xml",
            },
            # SiteListRequest endpoint
            "/foo.hts": {
                "Service=Hilltop&Request=SiteList": "site_list/all_response.xml",
            },
            # MeasurementListRequest endpoint
            "/foo.hts": {
                "Service=Hilltop&Request=MeasurementList": "measurement_list/all_response.xml",
            },
            # GetDataRequest endpoint
            "/foo.hts": {
                "Service=Hilltop&Request=GetData": "get_data/basic_response.xml",
            },
        }

        self._setup_routes()

    def _setup_routes(self):
        """Setup FastAPI routes."""

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "server": "whurl-performance-test"}

        @self.app.get("/foo.hts")
        async def hilltop_endpoint(service: str = None, request: str = None):
            """Provide Main Hilltop-compatible endpoint."""
            # Simulate artificial delay if configured
            if self.default_delay > 0:
                await asyncio.sleep(self.default_delay)

            # Simulate errors if configured
            if self.error_rate > 0 and time.time() % 1.0 < self.error_rate:
                raise HTTPException(status_code=500, detail="Simulated server error")

            # Handle case where parameters might be case-insensitive
            if not service:
                service = "Hilltop"  # Default service
            if not request:
                request = "Status"  # Default request

            # Create query key for fixture mapping
            query_key = f"Service={service}&Request={request}"

            # Find matching fixture
            fixture_file = None
            if query_key in self.fixture_mapping.get("/foo.hts", {}):
                fixture_file = self.fixture_mapping["/foo.hts"][query_key]
            else:
                # Default fallback - try to find any matching fixture
                if request == "Status":
                    fixture_file = "status/response.xml"
                elif request == "SiteList":
                    fixture_file = "site_list/all_response.xml"
                elif request == "MeasurementList":
                    fixture_file = "measurement_list/all_response.xml"
                elif request == "GetData":
                    fixture_file = "get_data/basic_response.xml"

            if not fixture_file:
                # Fallback to default response
                fixture_file = "status/response.xml"

            # Load fixture content
            fixture_path = self.mocked_data_path / fixture_file
            if not fixture_path.exists():
                # Create a minimal default response if fixture doesn't exist
                default_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<HilltopServer>
    <Agency>Test</Agency>
    <Version>MockServer-1.0</Version>
    <ScriptName>foo.hts</ScriptName>
    <ProcessID>12345</ProcessID>
    <DataFile>
        <Filename>test.dsn</Filename>
        <UsageCount>1</UsageCount>
    </DataFile>
</HilltopServer>"""
                return PlainTextResponse(content=default_xml, media_type="text/xml")

            try:
                xml_content = fixture_path.read_text(encoding="utf-8")
                return PlainTextResponse(content=xml_content, media_type="text/xml")
            except Exception as e:
                # Fallback to default XML on error
                default_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<HilltopServer>
    <Agency>Test</Agency>
    <Version>MockServer-1.0</Version>
    <ScriptName>foo.hts</ScriptName>
    <ProcessID>12345</ProcessID>
    <DataFile>
        <Filename>test.dsn</Filename>
        <UsageCount>1</UsageCount>
    </DataFile>
</HilltopServer>"""
                return PlainTextResponse(content=default_xml, media_type="text/xml")

    def run(self, **kwargs):
        """Run the server."""
        # Set default values but allow override
        run_kwargs = {
            "host": self.host,
            "port": self.port,
            "log_level": "warning",  # Reduce noise during testing
        }
        run_kwargs.update(kwargs)

        uvicorn.run(self.app, **run_kwargs)

    async def run_async(self, **kwargs):
        """Run the server asynchronously."""
        config = uvicorn.Config(
            self.app, host=self.host, port=self.port, log_level="warning", **kwargs
        )
        server = uvicorn.Server(config)
        await server.serve()


def create_test_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    delay: float = 0.0,
    error_rate: float = 0.0,
) -> LocalTestServer:
    """Create a test server with specified configuration (Factory function)."""
    return LocalTestServer(
        host=host, port=port, default_delay=delay, error_rate=error_rate
    )


if __name__ == "__main__":
    # Allow running server directly for manual testing
    delay = float(os.getenv("TEST_SERVER_DELAY", "0.0"))
    error_rate = float(os.getenv("TEST_SERVER_ERROR_RATE", "0.0"))
    port = int(os.getenv("TEST_SERVER_PORT", "8000"))

    server = create_test_server(delay=delay, error_rate=error_rate, port=port)
    print(f"Starting WHURL Performance Test Server on http://127.0.0.1:{port}")
    print(f"Configuration: delay={delay}s, error_rate={error_rate}")
    server.run()
