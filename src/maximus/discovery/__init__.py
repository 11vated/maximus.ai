"""Package discovery system for Maximus UOSA.

This module enables Maximus to discover and evaluate packages from:
- PyPI (Python)
- npm (JavaScript/TypeScript)
- crates.io (Rust)
"""

from maximus.discovery.package_discovery import (
    PackageDiscovery,
    PackageInfo,
    get_package_discovery,
    RegistryScanner,
    PyPIRegistry,
    NPMRegistry,
    CratesIORegistry,
)

__all__ = [
    "PackageDiscovery",
    "PackageInfo",
    "get_package_discovery",
    "RegistryScanner",
    "PyPIRegistry",
    "NPMRegistry",
    "CratesIORegistry",
]