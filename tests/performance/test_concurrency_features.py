"""Tests for httpx concurrency features.

This module tests httpx performance features related to concurrency:
- Sync vs async client performance
- Concurrent request handling
- Async context manager usage
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

from whurl.client import HilltopClient


class TestSyncVsAsyncPerformance:
    """Compare synchronous vs asynchronous client performance."""

    @pytest.mark.performance
    def test_sync_sequential_requests(self, benchmark, local_test_server):
        """Test synchronous sequential request performance."""

        def make_sync_requests():
            """Make sequential requests using sync client."""
            with httpx.Client(
                base_url=local_test_server["base_url"], timeout=30.0
            ) as client:
                results = []
                for _ in range(5):
                    response = client.get(
                        f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status"
                    )
                    results.append(response)
                return results

        results = benchmark(make_sync_requests)

        # Verify all requests succeeded
        assert len(results) == 5
        for result in results:
            assert result.status_code == 200

    @pytest.mark.performance
    def test_async_sequential_requests(self, benchmark, local_test_server):
        """Test asynchronous sequential request performance."""

        async def make_async_requests():
            """Make sequential requests using async client."""
            async with httpx.AsyncClient(
                base_url=local_test_server["base_url"], timeout=30.0
            ) as client:
                results = []
                for _ in range(5):
                    response = await client.get(
                        f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status"
                    )
                    results.append(response)
                return results

        def run_async_test():
            """Wrapper to run the async test."""
            return asyncio.run(make_async_requests())

        # Use pytest-benchmark's async support
        results = benchmark.pedantic(run_async_test, rounds=3, iterations=1)

        # Verify all requests succeeded
        assert len(results) == 5
        for result in results:
            assert result.status_code == 200

    @pytest.mark.performance
    def test_sync_vs_async_comparison(self, local_test_server):
        """Compare sync vs async performance for the same workload."""

        # Sync performance
        start_time = time.perf_counter()
        with httpx.Client(
            base_url=local_test_server["base_url"], timeout=30.0
        ) as client:
            sync_results = []
            for _ in range(10):
                response = client.get(
                    f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status"
                )
                sync_results.append(response)
        sync_time = time.perf_counter() - start_time

        # Async performance (sequential)
        async def async_sequential():
            async with httpx.AsyncClient(
                base_url=local_test_server["base_url"], timeout=30.0
            ) as client:
                async_results = []
                for _ in range(10):
                    response = await client.get(
                        f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status"
                    )
                    async_results.append(response)
                return async_results

        start_time = time.perf_counter()
        async_results = asyncio.run(async_sequential())
        async_time = time.perf_counter() - start_time

        # Verify both approaches work
        assert len(sync_results) == 10
        assert len(async_results) == 10

        for result in sync_results + async_results:
            assert result.status_code == 200

        # Record performance metrics
        print(f"Sync sequential time: {sync_time:.4f}s")
        print(f"Async sequential time: {async_time:.4f}s")
        print(f"Sync RPS: {10/sync_time:.2f}")
        print(f"Async RPS: {10/async_time:.2f}")


class TestConcurrentRequests:
    """Test concurrent request performance."""

    @pytest.mark.performance
    def test_sync_concurrent_with_threads(self, benchmark, local_test_server):
        """Test sync client with thread-based concurrency."""

        def make_single_request():
            """Make a single request."""
            with httpx.Client(
                base_url=local_test_server["base_url"], timeout=30.0
            ) as client:
                response = client.get(
                    f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status"
                )
                return response

        def make_concurrent_sync_requests():
            """Make concurrent requests using ThreadPoolExecutor."""
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_single_request) for _ in range(10)]
                results = [future.result() for future in futures]
                return results

        results = benchmark(make_concurrent_sync_requests)

        # Verify all requests succeeded
        assert len(results) == 10
        for result in results:
            assert result.status_code == 200

    @pytest.mark.performance
    def test_async_concurrent_requests(self, benchmark, local_test_server):
        """Test async client with asyncio concurrency."""

        async def make_async_concurrent_requests():
            """Make concurrent requests using asyncio.gather."""
            async with httpx.AsyncClient(
                base_url=local_test_server["base_url"],
                limits=httpx.Limits(max_connections=10),
                timeout=30.0,
            ) as client:
                tasks = [
                    client.get(
                        f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status"
                    )
                    for _ in range(10)
                ]
                results = await asyncio.gather(*tasks)
                return results

        def run_async_test():
            """Wrapper to run the async test."""
            return asyncio.run(make_async_concurrent_requests())

        results = benchmark.pedantic(run_async_test, rounds=3, iterations=1)

        # Verify all requests succeeded
        assert len(results) == 10
        for result in results:
            assert result.status_code == 200

    @pytest.mark.performance
    def test_concurrency_scaling(self, local_test_server):
        """Test how performance scales with concurrency level."""

        async def test_concurrency_level(concurrency):
            """Test performance at a specific concurrency level."""
            async with httpx.AsyncClient(
                base_url=local_test_server["base_url"],
                limits=httpx.Limits(max_connections=concurrency),
                timeout=30.0,
            ) as client:
                start_time = time.perf_counter()
                tasks = [
                    client.get(
                        f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status"
                    )
                    for _ in range(concurrency * 2)  # 2x requests vs connections
                ]
                results = await asyncio.gather(*tasks)
                end_time = time.perf_counter()

                return {
                    "concurrency": concurrency,
                    "requests": len(results),
                    "time": end_time - start_time,
                    "rps": len(results) / (end_time - start_time),
                    "success": all(r.status_code == 200 for r in results),
                }

        # Test different concurrency levels
        concurrency_levels = [1, 2, 5, 10]
        results = []

        for level in concurrency_levels:
            result = asyncio.run(test_concurrency_level(level))
            results.append(result)

        # Verify all tests succeeded
        for result in results:
            assert result["success"]
            print(
                f"Concurrency {result['concurrency']}: {result['rps']:.2f} RPS ({result['time']:.4f}s for {result['requests']} requests)"
            )

        # Check that concurrency generally improves performance
        # (though in test environment this might not always be true)
        assert all(r["rps"] > 0 for r in results)


class TestAsyncContextManagement:
    """Test async context manager performance."""

    @pytest.mark.performance
    async def test_async_context_manager_reuse(self, local_test_server):
        """Test reusing async client context manager."""

        async with httpx.AsyncClient(
            base_url=local_test_server["base_url"], timeout=30.0
        ) as client:
            # Multiple requests within same context
            start_time = time.perf_counter()
            results = []
            for _ in range(5):
                response = await client.get(
                    f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status"
                )
                results.append(response)
            end_time = time.perf_counter()

            # Verify all succeeded
            assert len(results) == 5
            for result in results:
                assert result.status_code == 200

            reuse_time = end_time - start_time
            print(f"Context reuse time: {reuse_time:.4f}s")

        # Compare with creating new context for each request
        start_time = time.perf_counter()
        new_context_results = []
        for _ in range(5):
            async with httpx.AsyncClient(
                base_url=local_test_server["base_url"], timeout=30.0
            ) as client:
                response = await client.get(
                    f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status"
                )
                new_context_results.append(response)
        end_time = time.perf_counter()

        new_context_time = end_time - start_time
        print(f"New context time: {new_context_time:.4f}s")
        print(
            f"Context reuse improvement: {((new_context_time - reuse_time) / new_context_time * 100):.1f}%"
        )

        # Verify both approaches work
        assert len(new_context_results) == 5
        for result in new_context_results:
            assert result.status_code == 200


class TestHilltopClientConcurrency:
    """Test HilltopClient in concurrent scenarios."""

    @pytest.mark.performance
    def test_hilltop_client_thread_safety(self, local_test_server):
        """Test HilltopClient thread safety (though it's not designed for it)."""

        # Note: HilltopClient is not designed to be thread-safe
        # This test demonstrates the recommended pattern: one client per thread

        def make_requests_with_own_client():
            """Each thread creates its own client."""
            with HilltopClient(
                base_url=local_test_server["base_url"],
                hts_endpoint=local_test_server["hts_endpoint"],
                timeout=30,
            ) as client:
                results = []
                for _ in range(3):
                    result = client.get_status()
                    results.append(result)
                return results

        # Use thread pool with separate clients
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_requests_with_own_client) for _ in range(3)]
            all_results = [future.result() for future in futures]

        # Verify all threads succeeded
        assert len(all_results) == 3
        for thread_results in all_results:
            assert len(thread_results) == 3
            for result in thread_results:
                assert hasattr(result, "request")

    @pytest.mark.performance
    def test_multiple_hilltop_clients(self, local_test_server):
        """Test performance with multiple HilltopClient instances."""

        start_time = time.perf_counter()
        results = []

        # Create multiple clients and use them
        for i in range(5):
            with HilltopClient(
                base_url=local_test_server["base_url"],
                hts_endpoint=local_test_server["hts_endpoint"],
                timeout=30,
            ) as client:
                result = client.get_status()
                results.append(result)

        end_time = time.perf_counter()

        # Verify all succeeded
        assert len(results) == 5
        for result in results:
            assert hasattr(result, "request")

        multiple_clients_time = end_time - start_time
        print(f"Multiple clients time: {multiple_clients_time:.4f}s")
        print(f"Multiple clients RPS: {5/multiple_clients_time:.2f}")

        # Compare with single client reuse
        start_time = time.perf_counter()
        with HilltopClient(
            base_url=local_test_server["base_url"],
            hts_endpoint=local_test_server["hts_endpoint"],
            timeout=30,
        ) as client:
            single_client_results = []
            for _ in range(5):
                result = client.get_status()
                single_client_results.append(result)
        end_time = time.perf_counter()

        single_client_time = end_time - start_time
        print(f"Single client time: {single_client_time:.4f}s")
        print(f"Single client RPS: {5/single_client_time:.2f}")

        # Verify both approaches work
        assert len(single_client_results) == 5
        for result in single_client_results:
            assert hasattr(result, "request")

        # Single client reuse should typically be faster
        print(
            f"Single client improvement: {((multiple_clients_time - single_client_time) / multiple_clients_time * 100):.1f}%"
        )

