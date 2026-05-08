"""PyPI Discovery Connector for Maximus.

Handles package discovery workflow.
"""
import logging
from typing import Any, Dict, List

from maximus.discovery.pypi import get_pypi_client

logger = logging.getLogger(__name__)


async def discover_packages(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Discover packages matching the query.
    
    Args:
        query: Search term
        limit: Maximum results to return
        
    Returns:
        List of package information
    """
    client = get_pypi_client()
    return await client.search_packages(query, limit)


async def get_package_details(package_name: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a package.
    
    Args:
        package_name: Name of the package
        
    Returns:
        Package details or None
    """
    client = get_pypi_client()
    return await client.get_package_info(package_name)


def format_package_info(pkg: Dict[str, Any]) -> str:
    """Format package info for display."""
    name = pkg.get("name", "unknown")
    version = pkg.get("version", "?")
    summary = pkg.get("summary", "No description")
    stars = pkg.get("stars", 0)
    
    return f"{name} ({version}): {summary} [{stars}★]"