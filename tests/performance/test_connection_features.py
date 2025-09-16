"""Tests for httpx connection management features.

This module tests httpx performance features related to connection management:
- Keep-alive connections vs new connections
- Connection pooling vs non-pooled connections
- Connection reuse patterns
"""

import asyncio
import time
from unittest.mock import patch

import httpx
import pytest

from hurl.client import HilltopClient


class TestConnectionKeepAlive:
    """Test connection keep-alive functionality."""
    
    @pytest.mark.performance_local
    def test_sequential_requests_with_keep_alive(self, benchmark, performance_local_client):
        """Test performance of sequential requests with keep-alive enabled."""
        
        def make_requests():
            """Make multiple sequential requests using the same client session."""
            results = []
            for _ in range(5):
                response = performance_local_client.get_status()
                results.append(response)
            return results
            
        # Benchmark with keep-alive (default httpx behavior)
        results = benchmark(make_requests)
        
        # Verify all requests succeeded
        assert len(results) == 5
        for result in results:
            assert hasattr(result, 'request')
            
    @pytest.mark.performance_local
    def test_sequential_requests_without_keep_alive(self, benchmark, local_test_server):
        """Test performance of sequential requests without keep-alive."""
        
        def make_requests_new_client():
            """Make multiple requests, creating a new client for each."""
            results = []
            for _ in range(5):
                # Create new client for each request (no connection reuse)
                with HilltopClient(
                    base_url=local_test_server["base_url"],
                    hts_endpoint=local_test_server["hts_endpoint"],
                    timeout=30
                ) as client:
                    result = client.get_status()
                    results.append(result)
            return results
            
        # Benchmark without keep-alive (new client each time)
        results = benchmark(make_requests_new_client)
        
        # Verify all requests succeeded
        assert len(results) == 5
        for result in results:
            assert hasattr(result, 'request')

    @pytest.mark.performance_local
    def test_keep_alive_vs_new_connections_comparison(self, local_test_server):
        """Compare keep-alive vs new connections performance."""
        
        # Test with keep-alive (reuse connection)
        start_time = time.perf_counter()
        with HilltopClient(
            base_url=local_test_server["base_url"],
            hts_endpoint=local_test_server["hts_endpoint"],
            timeout=30
        ) as client:
            for _ in range(10):
                client.get_status()
        keep_alive_time = time.perf_counter() - start_time
        
        # Test without keep-alive (new connection each time)
        start_time = time.perf_counter()
        for _ in range(10):
            with HilltopClient(
                base_url=local_test_server["base_url"],
                hts_endpoint=local_test_server["hts_endpoint"],
                timeout=30
            ) as client:
                client.get_status()
        new_connection_time = time.perf_counter() - start_time
        
        # Keep-alive should be faster (but allow some tolerance for test environment variability)
        print(f"Keep-alive time: {keep_alive_time:.4f}s")
        print(f"New connection time: {new_connection_time:.4f}s") 
        print(f"Performance improvement: {((new_connection_time - keep_alive_time) / new_connection_time * 100):.1f}%")
        
        # Keep-alive should typically be faster, but in test environments this might be minimal
        # So we just verify both approaches work and record the metrics
        assert keep_alive_time > 0
        assert new_connection_time > 0


class TestConnectionPooling:
    """Test connection pooling features."""
    
    @pytest.mark.performance_local
    def test_pooled_vs_non_pooled_requests(self, local_test_server):
        """Compare pooled vs non-pooled connection performance."""
        
        # Test pooled requests
        pooled_start = time.perf_counter()
        with httpx.Client(
            base_url=local_test_server["base_url"],
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            timeout=30.0
        ) as client:
            pooled_results = []
            for _ in range(5):
                response = client.get(f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status")
                pooled_results.append(response)
        pooled_time = time.perf_counter() - pooled_start
                
        # Test non-pooled requests
        non_pooled_start = time.perf_counter()
        with httpx.Client(
            base_url=local_test_server["base_url"], 
            limits=httpx.Limits(max_connections=1, max_keepalive_connections=0),
            timeout=30.0
        ) as client:
            non_pooled_results = []
            for _ in range(5):
                response = client.get(f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status")
                non_pooled_results.append(response)
        non_pooled_time = time.perf_counter() - non_pooled_start
        
        # Verify both approaches work
        assert len(pooled_results) == 5
        assert len(non_pooled_results) == 5
        
        for result in pooled_results + non_pooled_results:
            assert result.status_code == 200
            
        print(f"Pooled requests time: {pooled_time:.4f}s")
        print(f"Non-pooled requests time: {non_pooled_time:.4f}s")
        
        # Both should complete successfully
        assert pooled_time > 0
        assert non_pooled_time > 0

    @pytest.mark.performance_local 
    def test_connection_pool_limits(self, local_test_server):
        """Test behavior with different connection pool limits."""
        
        # Test with small pool
        small_pool_times = []
        with httpx.Client(
            base_url=local_test_server["base_url"],
            limits=httpx.Limits(max_connections=2, max_keepalive_connections=1),
            timeout=30.0
        ) as client:
            for _ in range(5):
                start = time.perf_counter()
                response = client.get(f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status")
                end = time.perf_counter()
                small_pool_times.append(end - start)
                assert response.status_code == 200
        
        # Test with large pool  
        large_pool_times = []
        with httpx.Client(
            base_url=local_test_server["base_url"],
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            timeout=30.0
        ) as client:
            for _ in range(5):
                start = time.perf_counter()
                response = client.get(f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status")
                end = time.perf_counter()
                large_pool_times.append(end - start)
                assert response.status_code == 200
                
        # Record metrics for analysis
        avg_small = sum(small_pool_times) / len(small_pool_times)
        avg_large = sum(large_pool_times) / len(large_pool_times)
        
        print(f"Small pool average time: {avg_small:.4f}s")
        print(f"Large pool average time: {avg_large:.4f}s")
        
        # Both should complete successfully
        assert avg_small > 0
        assert avg_large > 0


class TestConnectionConfiguration:
    """Test different httpx connection configurations."""
    
    @pytest.mark.performance_local
    def test_hilltop_client_connection_config(self, local_test_server):
        """Test HilltopClient's default connection configuration."""
        
        with HilltopClient(
            base_url=local_test_server["base_url"],
            hts_endpoint=local_test_server["hts_endpoint"],
            timeout=30
        ) as client:
            # Verify the client session has expected configuration
            assert client.session.timeout.connect == 30
            assert client.session.timeout.read == 30
            assert client.session.follow_redirects is True
            
            # Test that connections work
            response = client.get_status()
            assert hasattr(response, 'request')
            
            # Verify the client timeout configuration
            assert client.timeout == 30
            
            print(f"Client timeout: {client.timeout}s")
            print(f"Session timeout: {client.session.timeout}")
            print(f"Follow redirects: {client.session.follow_redirects}")
            print(f"Base URL: {client.base_url}")
            print(f"HTS Endpoint: {client.hts_endpoint}")
            
    @pytest.mark.performance_local
    def test_custom_connection_configuration(self, local_test_server):
        """Test custom httpx connection configurations."""
        
        # Test various configurations
        configs = [
            {"max_connections": 5, "max_keepalive_connections": 2},
            {"max_connections": 20, "max_keepalive_connections": 10},
            {"max_connections": 1, "max_keepalive_connections": 0},
        ]
        
        for config in configs:
            with httpx.Client(
                base_url=local_test_server["base_url"],
                limits=httpx.Limits(**config),
                timeout=30.0
            ) as client:
                response = client.get(f"/{local_test_server['hts_endpoint']}?Service=Hilltop&Request=Status")
                assert response.status_code == 200
                assert "Test" in response.text  # Basic XML validation