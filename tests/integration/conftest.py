"""Integration test configuration."""

import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: marks tests that require Ollama (skipped by default)"
    )
