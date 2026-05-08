"""Tests for Package Discovery functionality."""
import asyncio
import pytest
from maximus.discovery.pypi import PyPIDiscovery, get_pypi_client
from maximus.discovery.connector import discover_packages, get_package_details, format_package_info


class TestPyPIDiscovery:
    """Tests for PyPI discovery client."""

    def test_client_initialization(self):
        """Test PyPI client can be created."""
        client = PyPIDiscovery()
        assert client is not None
        assert client.base_url == "https://pypi.org/pypi"

    def test_get_instance(self):
        """Test global client singleton."""
        client = get_pypi_client()
        assert client is not None
        assert isinstance(client, PyPIDiscovery)

    def test_mock_search(self):
        """Test mock search returns results."""
        client = PyPIDiscovery()
        result = asyncio.run(client._mock_search("redis client", limit=3))
        assert isinstance(result, list)
        assert len(result) <= 3

    def test_mock_search_empty(self):
        """Test search with unknown query."""
        client = PyPIDiscovery()
        result = asyncio.run(client._mock_search("nonexistent-package-xyz", limit=3))
        assert result == []

    def test_search_limit_respected(self):
        """Test search respects limit parameter."""
        client = PyPIDiscovery()
        result = asyncio.run(client._mock_search("redis client", limit=1))
        assert len(result) == 1


class TestDiscoverConnector:
    """Tests for discovery connector functions."""

    def test_discover_packages(self):
        """Test package discovery function."""
        result = asyncio.run(discover_packages("redis client", limit=3))
        assert isinstance(result, list)
        if result:
            assert "name" in result[0]

    def test_get_package_details(self):
        """Test getting package details."""
        # Use a well-known package
        result = asyncio.run(get_package_details("requests"))
        # May return None if network unavailable, but shouldn't crash
        assert result is None or isinstance(result, dict)

    def test_format_package_info(self):
        """Test formatting package info for display."""
        pkg = {
            "name": "test-package",
            "version": "1.0.0",
            "summary": "A test package",
            "stars": 100,
        }
        result = format_package_info(pkg)
        assert "test-package" in result
        assert "1.0.0" in result

    def test_format_package_info_minimal(self):
        """Test formatting with minimal fields."""
        pkg = {"name": "minimal"}
        result = format_package_info(pkg)
        assert "minimal" in result