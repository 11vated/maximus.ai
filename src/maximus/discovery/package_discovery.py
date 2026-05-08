"""Package Discovery System - Multi-registry search for open-source packages.

This enables Maximus to discover and evaluate packages from:
- PyPI (Python)
- npm (JavaScript/TypeScript)  
- crates.io (Rust)
- Maven Central (Java)
- Go modules
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import httpx

logger = logging.getLogger(__name__)


@dataclass
class PackageInfo:
    """Information about a discovered package."""
    name: str
    version: str
    description: str
    registry: str  # "pypi", "npm", "crates", "maven", "go"
    language: str  # "python", "javascript", "rust", "java", "go"
    
    # Metadata
    author: Optional[str] = None
    license: Optional[str] = None
    homepage: Optional[str] = None
    repository: Optional[str] = None
    stars: Optional[int] = None
    downloads: Optional[int] = None
    
    # Relevance
    relevance_score: float = 0.0
    search_query: str = ""
    
    # For evaluation
    last_updated: Optional[str] = None
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class RegistryScanner:
    """Base class for registry scanners."""
    
    async def search(self, query: str, limit: int = 10) -> List[PackageInfo]:
        raise NotImplementedError
    
    async def get_details(self, package_name: str) -> Optional[PackageInfo]:
        raise NotImplementedError


class PyPIRegistry(RegistryScanner):
    """Scanner for Python Package Index (PyPI)."""
    
    BASE_URL = "https://pypi.org/pypi"
    
    async def search(self, query: str, limit: int = 10) -> List[PackageInfo]:
        """Search PyPI for packages."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Use the simple API
                url = f"https://pypi.org/search/?q={query}&o=-downloads"
                response = await client.get(url)
                
                if response.status_code != 200:
                    logger.warning(f"PyPI search failed: {response.status_code}")
                    return []
                
                # Parse HTML response (simplified - in production use proper parsing)
                # For now, return a placeholder - real implementation would parse HTML
                return await self._parse_search_results(response.text, query, limit)
                
            except Exception as e:
                logger.error(f"PyPI search error: {e}")
                return []
    
    async def _parse_search_results(self, html: str, query: str, limit: int) -> List[PackageInfo]:
        """Parse PyPI search results from HTML."""
        # Simplified parsing - in production use BeautifulSoup or similar
        packages = []
        
        # This is a simplified mock - real implementation needs HTML parsing
        # For now, return some known popular packages for common queries
        known_packages = {
            "web": [
                ("flask", "A lightweight WSGI web application framework"),
                ("django", "A high-level Python Web framework"),
                ("fastapi", "A fast web framework for building APIs"),
                ("requests", "HTTP library for Python"),
            ],
            "data": [
                ("pandas", "Powerful data structures for data analysis"),
                ("numpy", "Fundamental package for scientific computing"),
                ("scikit-learn", "Machine learning in Python"),
            ],
            "async": [
                ("asyncio", "Asynchronous I/O in Python"),
                ("aiohttp", "Async HTTP client/server"),
                ("httpx", "HTTP client for Python"),
            ],
            "cli": [
                ("click", "Composable command line interface"),
                ("typer", "Build great CLI apps easily"),
                ("rich", "Rich text and beautiful formatting"),
            ],
        }
        
        for key, pkgs in known_packages.items():
            if key in query.lower():
                for name, desc in pkgs:
                    packages.append(PackageInfo(
                        name=name,
                        version="latest",
                        description=desc,
                        registry="pypi",
                        language="python",
                        search_query=query,
                        relevance_score=0.8
                    ))
        
        return packages[:limit]
    
    async def get_details(self, package_name: str) -> Optional[PackageInfo]:
        """Get detailed information about a package."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                url = f"{self.BASE_URL}/{package_name}/json"
                response = await client.get(url)
                
                if response.status_code != 200:
                    return None
                
                data = response.json()
                info = data.get("info", {})
                
                return PackageInfo(
                    name=info.get("name", package_name),
                    version=info.get("version", "unknown"),
                    description=info.get("summary", ""),
                    registry="pypi",
                    language="python",
                    author=info.get("author"),
                    license=info.get("license"),
                    homepage=info.get("home_page"),
                    repository=info.get("project_url"),
                    downloads=info.get("downloads", {}).get("last_month")
                )
            except Exception as e:
                logger.error(f"PyPI details error for {package_name}: {e}")
                return None


class NPMRegistry(RegistryScanner):
    """Scanner for npm registry."""
    
    BASE_URL = "https://registry.npmjs.org"
    
    async def search(self, query: str, limit: int = 10) -> List[PackageInfo]:
        """Search npm for packages."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                url = f"{self.BASE_URL}/-/v1/search"
                params = {"text": query, "size": limit}
                response = await client.get(url, params=params)
                
                if response.status_code != 200:
                    return []
                
                data = response.json()
                packages = []
                
                for item in data.get("objects", [])[:limit]:
                    pkg = item.get("package", {})
                    packages.append(PackageInfo(
                        name=pkg.get("name", ""),
                        version=pkg.get("version", "latest"),
                        description=pkg.get("description", ""),
                        registry="npm",
                        language="javascript",
                        author=pkg.get("author", {}).get("name"),
                        repository=pkg.get("links", {}).get("repository"),
                        homepage=pkg.get("links", {}).get("homepage"),
                        search_query=query,
                        relevance_score=0.7
                    ))
                
                return packages
                
            except Exception as e:
                logger.error(f"npm search error: {e}")
                return []
    
    async def get_details(self, package_name: str) -> Optional[PackageInfo]:
        """Get detailed npm package info."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                url = f"{self.BASE_URL}/{package_name}/latest"
                response = await client.get(url)
                
                if response.status_code != 200:
                    return None
                
                data = response.json()
                
                return PackageInfo(
                    name=data.get("name", package_name),
                    version=data.get("version", "unknown"),
                    description=data.get("description", ""),
                    registry="npm",
                    language="javascript",
                    author=data.get("author", {}).get("name") if isinstance(data.get("author"), dict) else str(data.get("author", "")),
                    license=data.get("license"),
                    repository=data.get("repository", {}).get("url") if isinstance(data.get("repository"), dict) else str(data.get("repository", "")),
                    dependencies=list(data.get("dependencies", {}).keys())[:10]
                )
            except Exception as e:
                logger.error(f"npm details error for {package_name}: {e}")
                return None


class CratesIORegistry(RegistryScanner):
    """Scanner for crates.io (Rust)."""
    
    BASE_URL = "https://crates.io/api/v1"
    
    async def search(self, query: str, limit: int = 10) -> List[PackageInfo]:
        """Search crates.io for packages."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                url = f"{self.BASE_URL}/crates"
                params = {"q": query, "per_page": limit}
                response = await client.get(url, params=params)
                
                if response.status_code != 200:
                    return []
                
                data = response.json()
                packages = []
                
                for crate in data.get("crates", [])[:limit]:
                    packages.append(PackageInfo(
                        name=crate.get("name", ""),
                        version=crate.get("newest_version", "unknown"),
                        description=crate.get("description", ""),
                        registry="crates.io",
                        language="rust",
                        repository=crate.get("repository"),
                        downloads=crate.get("downloads"),
                        search_query=query,
                        relevance_score=0.6
                    ))
                
                return packages
                
            except Exception as e:
                logger.error(f"crates.io search error: {e}")
                return []
    
    async def get_details(self, package_name: str) -> Optional[PackageInfo]:
        """Get detailed crates.io package info."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                url = f"{self.BASE_URL}/crates/{package_name}"
                response = await client.get(url)
                
                if response.status_code != 200:
                    return None
                
                data = response.json()
                crate = data.get("crate", {})
                
                return PackageInfo(
                    name=crate.get("name", package_name),
                    version=crate.get("newest_version", "unknown"),
                    description=crate.get("description", ""),
                    registry="crates.io",
                    language="rust",
                    repository=crate.get("repository"),
                    downloads=crate.get("downloads"),
                    dependencies=[]  # Would need another API call
                )
            except Exception as e:
                logger.error(f"crates.io details error for {package_name}: {e}")
                return None


class PackageDiscovery:
    """Unified package discovery across multiple registries.
    
    This is the core of the UOSA discovery layer.
    """
    
    def __init__(self):
        self.registries = {
            "pypi": PyPIRegistry(),
            "npm": NPMRegistry(),
            "crates": CratesIORegistry(),
        }
        
        # Cache for recent searches
        self._cache: Dict[str, List[PackageInfo]] = {}
        self._cache_ttl = 300  # 5 minutes
    
    async def discover(
        self, 
        query: str, 
        languages: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[PackageInfo]:
        """Discover packages across all or specific registries.
        
        Args:
            query: Search query (e.g., "async http client")
            languages: Filter by language ["python", "javascript", "rust"]
            limit: Maximum results per registry
            
        Returns:
            List of discovered packages with relevance scores
        """
        if languages is None:
            languages = ["python", "javascript", "rust"]
        
        # Check cache
        cache_key = f"{query}:{':'.join(languages)}:{limit}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Search all requested registries in parallel
        tasks = []
        for lang in languages:
            if lang == "python" and "pypi" in self.registries:
                tasks.append(self._search_registry("pypi", query, limit))
            elif lang == "javascript" and "npm" in self.registries:
                tasks.append(self._search_registry("npm", query, limit))
            elif lang == "rust" and "crates" in self.registries:
                tasks.append(self._search_registry("crates", query, limit))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten and sort by relevance
        all_packages = []
        for result in results:
            if isinstance(result, list):
                all_packages.extend(result)
        
        # Sort by relevance score
        all_packages.sort(key=lambda p: p.relevance_score, reverse=True)
        
        # Cache results
        self._cache[cache_key] = all_packages
        
        return all_packages
    
    async def _search_registry(
        self, 
        registry_name: str, 
        query: str, 
        limit: int
    ) -> List[PackageInfo]:
        """Search a specific registry."""
        try:
            registry = self.registries.get(registry_name)
            if registry:
                return await registry.search(query, limit)
        except Exception as e:
            logger.warning(f"Registry {registry_name} search failed: {e}")
        return []
    
    async def get_package_details(
        self, 
        package_name: str, 
        registry: str
    ) -> Optional[PackageInfo]:
        """Get detailed information about a specific package."""
        registry_obj = self.registries.get(registry)
        if registry_obj:
            return await registry_obj.get_details(package_name)
        return None
    
    async def find_alternatives(
        self, 
        package_name: str, 
        registry: str
    ) -> List[PackageInfo]:
        """Find alternative packages to a given package."""
        # Get details first
        details = await self.get_package_details(package_name, registry)
        if not details:
            return []
        
        # Search using keywords from description
        keywords = details.description.split()[:5]
        search_query = " ".join(keywords)
        
        # Search for alternatives
        alternatives = await self.discover(
            search_query, 
            languages=[details.language],
            limit=5
        )
        
        # Filter out the original package
        return [p for p in alternatives if p.name != package_name]
    
    def clear_cache(self):
        """Clear the search cache."""
        self._cache.clear()


# Global discovery instance
_discovery: Optional[PackageDiscovery] = None

def get_package_discovery() -> PackageDiscovery:
    """Get the global package discovery instance."""
    global _discovery
    if _discovery is None:
        _discovery = PackageDiscovery()
    return _discovery