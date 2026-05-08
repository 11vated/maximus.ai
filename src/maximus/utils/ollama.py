"""Ollama management and hardware detection.

Handles automatic Ollama startup and model selection based on hardware.
"""
import os
import sys
import logging
import subprocess
import time
import platform

logger = logging.getLogger(__name__)

# Model aliases
MODEL_ALIASES = {
    "7b": "qwen2.5-coder:7b",
    "14b": "qwen2.5-coder:14b",
    "fast": "codellama:7b",
    "smart": "qwen2.5-coder:14b",
    "think": "deepseek-r1:7b",
    "coder": "qwen2.5-coder:7b",
    "code": "qwen2.5-coder:7b",
}


def resolve_model(model: str) -> str:
    """Resolve model alias to full model name."""
    if not model:
        return None
    return MODEL_ALIASES.get(model.lower(), model)


def check_ollama_running() -> bool:
    """Check if Ollama is responding."""
    try:
        import httpx
        resp = httpx.get("http://localhost:11434/api/tags", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


def ensure_ollama_running(max_wait: int = 10) -> bool:
    """Ensure Ollama is running, start if not.
    
    Returns True if Ollama is running, False otherwise.
    """
    # Check if already running
    if check_ollama_running():
        logger.info("Ollama already running")
        return True
    
    # Try to start Ollama
    logger.info("Starting Ollama...")
    try:
        # Start Ollama serve in background
        if platform.system() == "Windows":
            subprocess.Popen(
                ["ollama", "serve"],
                creation=subprocess.CREATE_NEW_PROCESS_GROUP,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
        
        # Wait for startup
        for _ in range(max_wait):
            time.sleep(1)
            if check_ollama_running():
                logger.info("Ollama started successfully")
                return True
                
        logger.error("Ollama did not start in time")
        return False
        
    except FileNotFoundError:
        logger.error("Ollama not found. Please install from ollama.ai")
        return False
    except Exception as e:
        logger.error(f"Failed to start Ollama: {e}")
        return False


def detect_hardware() -> dict:
    """Detect hardware capabilities for model selection."""
    hardware = {
        "ram_gb": 0,
        "vram_gb": 0,
        "has_gpu": False,
        "is_apple_silicon": False,
        "os": platform.system().lower()
    }
    
    # Detect RAM
    try:
        import psutil
        hardware["ram_gb"] = psutil.virtual_memory().total / (1024**3)
    except ImportError:
        # Fallback: platform-specific detection
        if platform.system() == "Darwin":
            try:
                result = subprocess.run(
                    ["sysctl", "-n", "hw.memsize"],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    hardware["ram_gb"] = int(result.stdout.strip()) / (1024**3)
            except:
                pass
        elif platform.system() == "Linux":
            try:
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            hardware["ram_gb"] = int(line.split()[1]) / (1024**2)
                            break
            except:
                pass
        elif platform.system() == "Windows":
            # Windows fallback: try wmic
            try:
                result = subprocess.run(
                    ["wmic", "ComputerSystem", "get", "TotalPhysicalMemory"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if line.isdigit():
                            hardware["ram_gb"] = int(line) / (1024**3)
                            break
            except:
                # Last resort: try systeminfo
                try:
                    result = subprocess.run(
                        ["systeminfo"],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if "Total Physical Memory" in line:
                                # Parse "16,384 MB" format
                                import re
                                match = re.search(r'([\d,]+)\s+MB', line)
                                if match:
                                    mb = int(match.group(1).replace(',', ''))
                                    hardware["ram_gb"] = mb / 1024
                                break
                except:
                    pass
    
    # Detect Apple Silicon
    if platform.system() == "Darwin":
        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True, text=True
            )
            if "Apple" in result.stdout:
                hardware["is_apple_silicon"] = True
                # Apple Silicon typically has unified memory
                # Assume 8GB minimum available
                hardware["has_gpu"] = True
                hardware["vram_gb"] = min(hardware["ram_gb"], 16)  # Conservative
        except:
            pass
    
    # Detect NVIDIA GPU (Linux/Windows)
    if platform.system() in ["Linux", "Windows"]:
        # Try nvidia-smi first
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                vram = int(result.stdout.strip().split('\n')[0])
                hardware["vram_gb"] = vram / 1024
                hardware["has_gpu"] = True
        except:
            pass
        
        # If no NVIDIA GPU, try to detect integrated GPU (Windows)
        if platform.system() == "Windows" and not hardware["has_gpu"]:
            try:
                # Check for Intel GPU via wmic
                result = subprocess.run(
                    ["wmic", "path", "win32_VideoController", "get", "adapterram"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if line.isdigit() and int(line) > 0:
                            # Found GPU memory (often integrated graphics)
                            vram_bytes = int(line)
                            vram_mb = vram_bytes / (1024**2)
                            # Integrated graphics typically < 2GB, use conservative estimate
                            if vram_mb > 512:  # At least 512MB
                                hardware["vram_gb"] = min(vram_mb / 1024, 4)  # Cap at 4GB for integrated
                                hardware["has_gpu"] = True
                            break
            except:
                pass
    
    logger.info(f"Hardware detected: {hardware}")
    return hardware


def get_default_model() -> str:
    """Get default model based on hardware."""
    hardware = detect_hardware()
    
    # Selection logic from PRD
    if hardware["is_apple_silicon"]:
        return "qwen2.5-coder:7b"
    
    if hardware["has_gpu"]:
        vram = hardware["vram_gb"]
        if vram >= 8:
            return "qwen2.5-coder:14b"
        elif vram >= 6:
            return "qwen2.5-coder:14b"
        else:
            return "qwen2.5-coder:7b"
    
    # No GPU - use smaller model
    return "codellama:7b"


def list_available_models() -> list:
    """List models available in Ollama."""
    try:
        import httpx
        resp = httpx.get("http://localhost:11434/api/tags", timeout=5)
        if resp.status_code == 200:
            return [m["name"] for m in resp.json().get("models", [])]
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
    return []