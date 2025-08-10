"""Manages all Coolify Self-hosted-specific aspects of the deployment process.

Notes:
- ...
"""

import subprocess
from pathlib import Path
import django_simple_deploy

from .platform_deployer import PlatformDeployer
from .plugin_config import PluginConfig


def _ensure_requirements_txt_exists():
    """Generate requirements.txt for uv projects if it doesn't exist."""
    try:
        # Try to get the project root from environment or current directory
        import os
        project_root = Path(os.getcwd())
        
        pyproject_path = project_root / "pyproject.toml"
        uv_lock_path = project_root / "uv.lock"
        requirements_path = project_root / "requirements.txt"
        
        # If pyproject.toml and uv.lock exist but requirements.txt doesn't, this is likely a uv project
        if pyproject_path.exists() and uv_lock_path.exists() and not requirements_path.exists():
            try:
                # Run uv export to generate requirements.txt
                result = subprocess.run(
                    ["uv", "export", "--format", "requirements-txt"],
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Write the requirements to requirements.txt
                with open(requirements_path, 'w') as f:
                    f.write(result.stdout)
                
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Silently fail, let the framework handle the error
                pass
    except Exception:
        # Silently fail, let the framework handle the error
        pass


@django_simple_deploy.hookimpl
def dsd_get_plugin_config():
    """Get platform-specific attributes needed by core."""
    # Generate requirements.txt for uv projects before inspection
    _ensure_requirements_txt_exists()
    
    plugin_config = PluginConfig()
    return plugin_config


@django_simple_deploy.hookimpl
def dsd_deploy():
    """Carry out platform-specific deployment steps."""
    platform_deployer = PlatformDeployer()
    platform_deployer.deploy()
