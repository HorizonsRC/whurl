"""Tests for httpx timeout and retry configuration effects.

This module tests httpx performance characteristics related to:
- Different timeout configurations
- Retry behavior and performance impact
- Error handling and recovery
"""

import asyncio
import time
from unittest.mock import patch

import httpx
import pytest

from hurl.client import HilltopClient


class TestTimeoutConfiguration:
    """Test different timeout configuration effects."""
    
    @pytest.mark.performance_local
    def test_short_timeout_performance(self, benchmark, local_test_server):
        """Test performance with short timeout values."""
        
        def make_requests_short_timeout():
            """Make requests with short timeout."""
            with httpx.Client(
                base_url=local_test_server["base_url"],
                timeout=1.0,  # Very short timeout
            ) as client:
                results = []
                for _ in range(3):
                    try:
                        response = client.get(f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status")
                        results.append(response)
                    except httpx.TimeoutException:
                        # Count timeouts as results too
                        results.append(None)
                return results
                
        results = benchmark(make_requests_short_timeout)
        
        # Should have attempted all requests
        assert len(results) == 3
        
        # Count successful vs timeout responses
        successful = [r for r in results if r is not None and r.status_code == 200]
        timeouts = [r for r in results if r is None]
        
        print(f"Successful requests: {len(successful)}")
        print(f"Timeout requests: {len(timeouts)}")
    
    @pytest.mark.performance_local
    def test_long_timeout_performance(self, benchmark, local_test_server):
        """Test performance with long timeout values."""
        
        def make_requests_long_timeout():
            """Make requests with long timeout."""
            with httpx.Client(
                base_url=local_test_server["base_url"],
                timeout=30.0,  # Long timeout
            ) as client:
                results = []
                for _ in range(3):
                    response = client.get(f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status")
                    results.append(response)
                return results
                
        results = benchmark(make_requests_long_timeout)
        
        # All should succeed with long timeout
        assert len(results) == 3
        for result in results:
            assert result.status_code == 200
    
    @pytest.mark.performance_local
    def test_timeout_granularity(self, local_test_server):
        """Test different timeout granularity settings."""
        
        # Test fine-grained timeout configuration
        timeout_config = httpx.Timeout(
            connect=5.0,    # Connection timeout
            read=10.0,      # Read timeout
            write=5.0,      # Write timeout  
            pool=15.0       # Pool timeout
        )
        
        start_time = time.perf_counter()
        with httpx.Client(
            base_url=local_test_server["base_url"],
            timeout=timeout_config
        ) as client:
            results = []
            for _ in range(5):
                response = client.get(f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status")
                results.append(response)
        end_time = time.perf_counter()
        
        # Verify all succeeded
        assert len(results) == 5
        for result in results:
            assert result.status_code == 200
            
        granular_time = end_time - start_time
        print(f"Granular timeout time: {granular_time:.4f}s")
        
        # Compare with simple timeout
        start_time = time.perf_counter()
        with httpx.Client(
            base_url=local_test_server["base_url"],
            timeout=30.0  # Simple timeout
        ) as client:
            simple_results = []
            for _ in range(5):
                response = client.get(f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status")
                simple_results.append(response)
        end_time = time.perf_counter()
        
        simple_time = end_time - start_time
        print(f"Simple timeout time: {simple_time:.4f}s")
        
        # Both should work similarly for successful requests
        assert len(simple_results) == 5
        for result in simple_results:
            assert result.status_code == 200


class TestRetryBehavior:
    """Test retry behavior and its performance impact."""
    
    @pytest.mark.performance_local
    def test_no_retry_performance(self, benchmark, local_test_server):
        """Test performance without retry logic."""
        
        def make_requests_no_retry():
            """Make requests without any retry logic."""
            with httpx.Client(
                base_url=local_test_server["base_url"],
                timeout=30.0
            ) as client:
                results = []
                for _ in range(5):
                    response = client.get(f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status")
                    results.append(response)
                return results
                
        results = benchmark(make_requests_no_retry)
        
        assert len(results) == 5
        for result in results:
            assert result.status_code == 200
    
    @pytest.mark.performance_local
    def test_manual_retry_performance(self, benchmark, local_test_server):
        """Test performance with manual retry logic."""
        
        def make_requests_with_retry():
            """Make requests with manual retry logic."""
            with httpx.Client(
                base_url=local_test_server["base_url"],
                timeout=5.0
            ) as client:
                results = []
                for _ in range(3):  # Fewer requests since we're adding retry overhead
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            response = client.get(f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status")
                            results.append(response)
                            break  # Success, no need to retry
                        except (httpx.TimeoutException, httpx.RequestError) as e:
                            if attempt == max_retries - 1:
                                # Last attempt failed, record the failure
                                results.append(None)
                            else:
                                # Wait before retry
                                time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                return results
                
        results = benchmark(make_requests_with_retry)
        
        assert len(results) == 3
        successful = [r for r in results if r is not None and r.status_code == 200]
        failed = [r for r in results if r is None]
        
        print(f"Successful with retry: {len(successful)}")
        print(f"Failed after retries: {len(failed)}")
    
    @pytest.mark.performance_local
    def test_retry_vs_no_retry_comparison(self, local_test_server):
        """Compare performance with and without retry logic."""
        
        # Test without retry
        start_time = time.perf_counter()
        with httpx.Client(
            base_url=local_test_server["base_url"],
            timeout=30.0
        ) as client:
            no_retry_results = []
            for _ in range(5):
                response = client.get(f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status")
                no_retry_results.append(response)
        no_retry_time = time.perf_counter() - start_time
        
        # Test with retry logic
        start_time = time.perf_counter()
        with httpx.Client(
            base_url=local_test_server["base_url"],
            timeout=30.0
        ) as client:
            retry_results = []
            for _ in range(5):
                max_retries = 2
                for attempt in range(max_retries):
                    try:
                        response = client.get(f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status")
                        retry_results.append(response)
                        break
                    except (httpx.TimeoutException, httpx.RequestError):
                        if attempt == max_retries - 1:
                            retry_results.append(None)
                        else:
                            time.sleep(0.05)  # Small delay between retries
        retry_time = time.perf_counter() - start_time
        
        # Both should succeed in this case (no network errors expected)
        assert len(no_retry_results) == 5
        assert len(retry_results) == 5
        
        for result in no_retry_results + retry_results:
            if result is not None:
                assert result.status_code == 200
                
        print(f"No retry time: {no_retry_time:.4f}s")
        print(f"With retry time: {retry_time:.4f}s")
        print(f"Retry overhead: {((retry_time - no_retry_time) / no_retry_time * 100):.1f}%")


class TestErrorHandlingPerformance:
    """Test error handling and recovery performance."""
    
    @pytest.mark.performance_local
    def test_connection_error_handling(self, local_test_server):
        """Test performance when handling connection errors."""
        
        # Test requests to a non-existent endpoint
        invalid_url = local_test_server["base_url"].replace("8001", "9999")  # Wrong port
        
        start_time = time.perf_counter()
        error_count = 0
        with httpx.Client(timeout=1.0) as client:
            for _ in range(3):
                try:
                    response = client.get(f"{invalid_url}/foo.hts?Service=Hilltop&Request=Status")
                except (httpx.ConnectError, httpx.TimeoutException):
                    error_count += 1
        error_handling_time = time.perf_counter() - start_time
        
        print(f"Error handling time: {error_handling_time:.4f}s")
        print(f"Errors encountered: {error_count}")
        
        # Should have encountered connection errors
        assert error_count > 0
    
    @pytest.mark.performance_local
    def test_mixed_success_failure_performance(self, local_test_server):
        """Test performance with mixed successful and failed requests."""
        
        # Simulate a scenario with some failing requests
        start_time = time.perf_counter()
        results = []
        
        with httpx.Client(timeout=2.0) as client:
            # Mix of valid and invalid requests
            requests = [
                f"{local_test_server['base_url']}/foo.hts?Service=Hilltop&Request=Status",  # Valid
                f"{local_test_server['base_url']}/invalid?Service=Hilltop&Request=Status",  # Invalid endpoint
                f"{local_test_server['base_url']}/foo.hts?Service=Hilltop&Request=Status",  # Valid
                f"{local_test_server['base_url']}/foo.hts?Invalid=Request",  # Invalid params
                f"{local_test_server['base_url']}/foo.hts?Service=Hilltop&Request=Status",  # Valid
            ]
            
            for url in requests:
                try:
                    response = client.get(url)
                    results.append(('success', response.status_code))
                except httpx.RequestError as e:
                    results.append(('error', str(type(e).__name__)))
                    
        mixed_time = time.perf_counter() - start_time
        
        # Count successes and failures
        successes = [r for r in results if r[0] == 'success' and r[1] == 200]
        failures = [r for r in results if r[0] == 'error' or (r[0] == 'success' and r[1] != 200)]
        
        print(f"Mixed requests time: {mixed_time:.4f}s")
        print(f"Successful requests: {len(successes)}")
        print(f"Failed requests: {len(failures)}")
        
        # Should have a mix of successes and failures
        assert len(results) == 5
        assert len(successes) > 0  # Some requests should succeed
        assert len(failures) > 0   # Some requests should fail


class TestHilltopClientTimeoutBehavior:
    """Test HilltopClient timeout behavior."""
    
    @pytest.mark.performance_local
    def test_hilltop_client_default_timeout(self, local_test_server):
        """Test HilltopClient with default timeout configuration."""
        
        start_time = time.perf_counter()
        with HilltopClient(
            base_url=local_test_server["base_url"],
            hts_endpoint=local_test_server["hts_endpoint"],
            timeout=60  # Default timeout
        ) as client:
            results = []
            for _ in range(3):
                result = client.get_status()
                results.append(result)
        default_timeout_time = time.perf_counter() - start_time
        
        assert len(results) == 3
        for result in results:
            assert hasattr(result, 'request')
            
        print(f"Default timeout (60s) time: {default_timeout_time:.4f}s")
    
    @pytest.mark.performance_local
    def test_hilltop_client_custom_timeout(self, local_test_server):
        """Test HilltopClient with custom timeout configuration."""
        
        # Test with shorter timeout
        start_time = time.perf_counter()
        with HilltopClient(
            base_url=local_test_server["base_url"],
            hts_endpoint=local_test_server["hts_endpoint"],
            timeout=10  # Custom shorter timeout
        ) as client:
            results = []
            for _ in range(3):
                result = client.get_status()
                results.append(result)
        custom_timeout_time = time.perf_counter() - start_time
        
        assert len(results) == 3
        for result in results:
            assert hasattr(result, 'request')
            
        print(f"Custom timeout (10s) time: {custom_timeout_time:.4f}s")
        
        # For successful requests, timeout value shouldn't significantly affect performance
        # (the actual network operations are the same)
        assert custom_timeout_time > 0
    
    @pytest.mark.performance_local
    def test_hilltop_client_timeout_configuration(self, local_test_server):
        """Test that HilltopClient correctly configures httpx timeout."""
        
        timeout_value = 15
        with HilltopClient(
            base_url=local_test_server["base_url"],
            hts_endpoint=local_test_server["hts_endpoint"],
            timeout=timeout_value
        ) as client:
            # Verify the timeout is correctly configured in the underlying session
            assert client.timeout == timeout_value
            assert client.session.timeout.timeout == timeout_value
            
            # Make a request to ensure it works
            result = client.get_status()
            assert hasattr(result, 'request')


class TestAsyncTimeoutBehavior:
    """Test async client timeout behavior."""
    
    @pytest.mark.performance_local
    async def test_async_client_timeout_performance(self, local_test_server):
        """Test async client timeout performance."""
        
        # Test with various timeout configurations
        timeout_configs = [5.0, 10.0, 30.0]
        
        for timeout in timeout_configs:
            start_time = time.perf_counter()
            async with httpx.AsyncClient(
                base_url=local_test_server["base_url"],
                timeout=timeout
            ) as client:
                tasks = [
                    client.get(f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status")
                    for _ in range(3)
                ]
                results = await asyncio.gather(*tasks)
            end_time = time.perf_counter()
            
            # Verify all succeeded
            assert len(results) == 3
            for result in results:
                assert result.status_code == 200
                
            async_time = end_time - start_time
            print(f"Async timeout {timeout}s time: {async_time:.4f}s")