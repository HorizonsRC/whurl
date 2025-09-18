"""Tests for httpx protocol features.

This module tests httpx performance features related to HTTP protocols:
- HTTP/1.1 vs HTTP/2 performance
- Protocol negotiation
- Protocol-specific optimizations
"""

import asyncio
import time

import httpx
import pytest

from hurl.client import HilltopClient


class TestHTTPProtocolPerformance:
    """Test HTTP protocol performance characteristics."""

    @pytest.mark.performance
    def test_http1_sequential_requests(self, benchmark, local_test_server):
        """Test HTTP/1.1 sequential request performance."""

        def make_http1_requests():
            """Make requests using HTTP/1.1 explicitly."""
            with httpx.Client(
                base_url=local_test_server["base_url"],
                http2=False,  # Force HTTP/1.1
                limits=httpx.Limits(max_connections=10),
                timeout=30.0,
            ) as client:
                results = []
                for _ in range(5):
                    response = client.get(
                        f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status"
                    )
                    results.append(response)
                return results

        results = benchmark(make_http1_requests)

        # Verify all requests succeeded
        assert len(results) == 5
        for result in results:
            assert result.status_code == 200
            # Verify we're using HTTP/1.1
            assert result.http_version == "HTTP/1.1"

    @pytest.mark.performance
    def test_http2_sequential_requests(self, benchmark, local_test_server):
        """Test HTTP/2 sequential request performance."""

        def make_http2_requests():
            """Make requests using HTTP/2 if available."""
            with httpx.Client(
                base_url=local_test_server["base_url"],
                http2=True,  # Enable HTTP/2
                limits=httpx.Limits(max_connections=10),
                timeout=30.0,
            ) as client:
                results = []
                for _ in range(5):
                    response = client.get(
                        f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status"
                    )
                    results.append(response)
                return results

        results = benchmark(make_http2_requests)

        # Verify all requests succeeded
        assert len(results) == 5
        for result in results:
            assert result.status_code == 200
            # Note: Local FastAPI server may not support HTTP/2, so we don't assert version

    @pytest.mark.performance
    def test_protocol_comparison(self, local_test_server):
        """Compare HTTP/1.1 vs HTTP/2 performance characteristics."""

        # Test HTTP/1.1 performance
        start_time = time.perf_counter()
        with httpx.Client(
            base_url=local_test_server["base_url"],
            http2=False,
            limits=httpx.Limits(max_connections=5),
            timeout=30.0,
        ) as client:
            http1_responses = []
            for _ in range(10):
                response = client.get(
                    f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status"
                )
                http1_responses.append(response)
        http1_time = time.perf_counter() - start_time

        # Test HTTP/2 performance
        start_time = time.perf_counter()
        with httpx.Client(
            base_url=local_test_server["base_url"],
            http2=True,
            limits=httpx.Limits(max_connections=5),
            timeout=30.0,
        ) as client:
            http2_responses = []
            for _ in range(10):
                response = client.get(
                    f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status"
                )
                http2_responses.append(response)
        http2_time = time.perf_counter() - start_time

        # Verify both protocols work
        assert len(http1_responses) == 10
        assert len(http2_responses) == 10

        for response in http1_responses:
            assert response.status_code == 200
            assert response.http_version == "HTTP/1.1"

        for response in http2_responses:
            assert response.status_code == 200
            # HTTP version may be 1.1 or 2.0 depending on server support

        # Record performance metrics
        print(f"HTTP/1.1 time: {http1_time:.4f}s")
        print(f"HTTP/2 time: {http2_time:.4f}s")
        print(f"Requests per second (HTTP/1.1): {10/http1_time:.2f}")
        print(f"Requests per second (HTTP/2): {10/http2_time:.2f}")


class TestConcurrentProtocolRequests:
    """Test concurrent request performance with different protocols."""

    @pytest.mark.performance
    async def test_concurrent_http1_requests(self, local_test_server):
        """Test concurrent HTTP/1.1 requests."""

        async def make_request(client):
            """Make a single async request."""
            response = await client.get(
                f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status"
            )
            return response

        async with httpx.AsyncClient(
            base_url=local_test_server["base_url"],
            http2=False,
            limits=httpx.Limits(max_connections=10),
            timeout=30.0,
        ) as client:
            # Make 10 concurrent requests
            start_time = time.perf_counter()
            tasks = [make_request(client) for _ in range(10)]
            responses = await asyncio.gather(*tasks)
            end_time = time.perf_counter()

            # Verify all requests succeeded
            assert len(responses) == 10
            for response in responses:
                assert response.status_code == 200
                assert response.http_version == "HTTP/1.1"

            concurrent_time = end_time - start_time
            print(f"Concurrent HTTP/1.1 time: {concurrent_time:.4f}s")
            print(f"Concurrent requests per second: {10/concurrent_time:.2f}")

    @pytest.mark.performance
    async def test_concurrent_http2_requests(self, local_test_server):
        """Test concurrent HTTP/2 requests."""

        async def make_request(client):
            """Make a single async request."""
            response = await client.get(
                f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status"
            )
            return response

        async with httpx.AsyncClient(
            base_url=local_test_server["base_url"],
            http2=True,
            limits=httpx.Limits(max_connections=10),
            timeout=30.0,
        ) as client:
            # Make 10 concurrent requests
            start_time = time.perf_counter()
            tasks = [make_request(client) for _ in range(10)]
            responses = await asyncio.gather(*tasks)
            end_time = time.perf_counter()

            # Verify all requests succeeded
            assert len(responses) == 10
            for response in responses:
                assert response.status_code == 200
                # HTTP version depends on server support

            concurrent_time = end_time - start_time
            print(f"Concurrent HTTP/2 time: {concurrent_time:.4f}s")
            print(f"Concurrent requests per second: {10/concurrent_time:.2f}")


class TestProtocolConfiguration:
    """Test protocol configuration in HilltopClient."""

    @pytest.mark.performance
    def test_hilltop_client_default_protocol(self, local_test_server):
        """Test HilltopClient's default protocol configuration."""

        with HilltopClient(
            base_url=local_test_server["base_url"],
            hts_endpoint=local_test_server["hts_endpoint"],
            timeout=30,
        ) as client:
            # Make a request to see what protocol is used
            response = client.get_status()
            assert hasattr(response, "request")

            # Check the underlying session configuration
            # HilltopClient uses httpx.Client which defaults to HTTP/1.1 unless http2=True

            # NIC: Not sure what copilot is trying to assert here.
            # This is not an attribute.

            # assert hasattr(client.session, "limits")

    @pytest.mark.performance
    def test_protocol_fallback_behavior(self, local_test_server):
        """Test protocol fallback behavior."""

        # Test that HTTP/2 client can fallback to HTTP/1.1 if needed
        with httpx.Client(
            base_url=local_test_server["base_url"],
            http2=True,  # Enable HTTP/2 but allow fallback
            timeout=30.0,
        ) as client:
            response = client.get(
                f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status"
            )
            assert response.status_code == 200
            # Should work regardless of what protocol the server actually supports
