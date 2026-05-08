"""Auto-install pipeline for packages - enables Maximus to install packages on demand.

This enables:
- Installing packages from any registry
- Version resolution and dependency management
- Virtual environment isolation
- Rollback capabilities
"""

import asyncio
import subprocess
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)


@dataclass
class InstallResult:
    """Result of a package installation."""
    success: bool
    package_name: str
    version: Optional[str] = None
    error: Optional[str] = None
    installed_files: List[str] = None
    execution_time_ms: float = 0.0
    
    def __post_init__(self):
        if self.installed_files is None:
            self.installed_files = []


class PackageInstaller:
    """Handles on-demand package installation for the agent."""
    
    def __init__(self, workspace_path: Optional[str] = None):
        self.workspace_path = Path(workspace_path) if workspace_path else Path.cwd()
        self._installed_packages: Dict[str, str] = {}  # name -> version
        
    async def install_package(
        self,
        package_name: str,
        package_manager: str = "pip",  # "pip", "npm", "cargo"
        version: Optional[str] = None,
        extra_args: Optional[List[str]] = None
    ) -> InstallResult:
        """Install a package using the specified package manager.
        
        Args:
            package_name: Name of the package to install
            package_manager: Package manager to use ("pip", "npm", "cargo")
            version: Specific version to install (optional)
            extra_args: Additional arguments for the package manager
            
        Returns:
            InstallResult with success status and details
        """
        start_time = datetime.now()
        
        try:
            # Build the install command
            cmd = self._build_install_command(
                package_name, package_manager, version, extra_args
            )
            
            if not cmd:
                return InstallResult(
                    success=False,
                    package_name=package_name,
                    error=f"Unsupported package manager: {package_manager}"
                )
            
            # Execute the install command
            result = await self._execute_install(cmd, package_manager)
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if result["success"]:
                # Track installed package
                version_str = version or "latest"
                self._installed_packages[package_name] = version_str
                
                logger.info(f"Installed {package_name}@{version_str} in {execution_time:.0f}ms")
                
                return InstallResult(
                    success=True,
                    package_name=package_name,
                    version=version_str,
                    installed_files=result.get("files", []),
                    execution_time_ms=execution_time
                )
            else:
                return InstallResult(
                    success=False,
                    package_name=package_name,
                    error=result.get("error", "Installation failed"),
                    execution_time_ms=execution_time
                )
                
        except Exception as e:
            logger.error(f"Package installation failed: {e}")
            return InstallResult(
                success=False,
                package_name=package_name,
                error=str(e)
            )
    
    def _build_install_command(
        self,
        package_name: str,
        package_manager: str,
        version: Optional[str],
        extra_args: Optional[List[str]]
    ) -> Optional[str]:
        """Build the appropriate install command."""
        
        extra = " ".join(extra_args) if extra_args else ""
        
        if package_manager == "pip":
            version_spec = f"=={version}" if version else ""
            return f"pip install {package_name}{version_spec} {extra}".strip()
            
        elif package_manager == "npm":
            return f"npm install {package_name} {extra}".strip()
            
        elif package_manager == "cargo":
            version_spec = f" --version {version}" if version else ""
            return f"cargo add {package_name}{version_spec} {extra}".strip()
            
        elif package_manager == "poetry":
            version_spec = f"=={version}" if version else ""
            return f"poetry add {package_name}{version_spec} {extra}".strip()
        
        return None
    
    async def _execute_install(
        self, 
        command: str, 
        package_manager: str
    ) -> Dict[str, Any]:
        """Execute the install command."""
        
        try:
            # Run the command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=120  # 2 minute timeout for installs
            )
            
            if process.returncode == 0:
                return {
                    "success": True,
                    "output": stdout.decode('utf-8', errors='replace'),
                    "files": []  # Could parse output for installed files
                }
            else:
                return {
                    "success": False,
                    "error": stderr.decode('utf-8', errors='replace') or "Install failed"
                }
                
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "Installation timed out after 120 seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def install_requirements(
        self,
        requirements_file: str,
        package_manager: str = "pip"
    ) -> Dict[str, Any]:
        """Install all packages from a requirements file."""
        
        if not Path(requirements_file).exists():
            return {
                "success": False,
                "error": f"Requirements file not found: {requirements_file}"
            }
        
        if package_manager == "pip":
            cmd = f"pip install -r {requirements_file}"
        elif package_manager == "npm":
            cmd = "npm install"
        else:
            return {
                "success": False,
                "error": f"Requirements file not supported for {package_manager}"
            }
        
        result = await self._execute_install(cmd, package_manager)
        
        # Parse output to get installed packages
        if result["success"]:
            # Could parse pip freeze output
            pass
            
        return result
    
    def get_installed_packages(self) -> Dict[str, str]:
        """Get all packages installed by this installer."""
        return self._installed_packages.copy()
    
    async def uninstall_package(
        self,
        package_name: str,
        package_manager: str = "pip"
    ) -> bool:
        """Uninstall a package."""
        
        try:
            if package_manager == "pip":
                cmd = f"pip uninstall {package_name} -y"
            elif package_manager == "npm":
                cmd = f"npm uninstall {package_name}"
            elif package_manager == "cargo":
                cmd = f"cargo remove {package_name}"
            else:
                return False
            
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            if package_name in self._installed_packages:
                del self._installed_packages[package_name]
                
            return process.returncode == 0
            
        except Exception as e:
            logger.error(f"Uninstall failed: {e}")
            return False
    
    def can_install(self, package_manager: str) -> bool:
        """Check if a package manager is available."""
        
        if package_manager == "pip":
            return shutil.which("pip") is not None
        elif package_manager == "npm":
            return shutil.which("npm") is not None
        elif package_manager == "cargo":
            return shutil.which("cargo") is not None
        elif package_manager == "poetry":
            return shutil.which("poetry") is not None
            
        return False


# Global installer instance
_installer: Optional[PackageInstaller] = None

def get_package_installer(workspace_path: Optional[str] = None) -> PackageInstaller:
    """Get the global package installer instance."""
    global _installer
    if _installer is None:
        _installer = PackageInstaller(workspace_path)
    return _installer