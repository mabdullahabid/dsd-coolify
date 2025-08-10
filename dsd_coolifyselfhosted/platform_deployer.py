"""Manages all Coolify Self-hosted-specific aspects of the deployment process.

Notes:
- 

Add a new file to the user's project, without using a template:

    def _add_dockerignore(self):
        # Add a dockerignore file, based on user's local project environmnet.
        path = dsd_config.project_root / ".dockerignore"
        dockerignore_str = self._build_dockerignore()
        plugin_utils.add_file(path, dockerignore_str)

Add a new file to the user's project, using a template:

    def _add_dockerfile(self):
        # Add a minimal dockerfile.
        template_path = self.templates_path / "dockerfile_example"
        context = {
            "django_project_name": dsd_config.local_project_name,
        }
        contents = plugin_utils.get_template_string(template_path, context)

        # Write file to project.
        path = dsd_config.project_root / "Dockerfile"
        plugin_utils.add_file(path, contents)

Modify user's settings file:

    def _modify_settings(self):
        # Add platformsh-specific settings.
        template_path = self.templates_path / "settings.py"
        context = {
            "deployed_project_name": self._get_deployed_project_name(),
        }
        plugin_utils.modify_settings_file(template_path, context)

Add a set of requirements:

    def _add_requirements(self):
        # Add requirements for deploying to Fly.io.
        requirements = ["gunicorn", "psycopg2-binary", "dj-database-url", "whitenoise"]
        plugin_utils.add_packages(requirements)
"""

import sys, os, re, json
from pathlib import Path

from django.utils.safestring import mark_safe

import requests

from . import deploy_messages as platform_msgs

from django_simple_deploy.management.commands.utils import plugin_utils
from django_simple_deploy.management.commands.utils.plugin_utils import dsd_config
from django_simple_deploy.management.commands.utils.command_errors import DSDCommandError


class PlatformDeployer:
    """Perform the initial deployment to Coolify Self-hosted

    If --automate-all is used, carry out an actual deployment.
    If not, do all configuration work so the user only has to commit changes, and ...
    """

    def __init__(self):
        self.templates_path = Path(__file__).parent / "templates"
        self.deployed_url = None

    # --- Public methods ---

    def deploy(self, *args, **options):
        """Coordinate the overall configuration and deployment."""
        plugin_utils.write_output("\nConfiguring project for deployment to Coolify Self-hosted...")

        self._validate_platform()
        self._prep_automate_all()

        # Configure project for deployment to Coolify Self-hosted
        self._add_dockerfile()
        self._add_dockerignore()
        self._modify_settings()
        self._add_requirements()

        self._conclude_automate_all()
        self._show_success_message()

    # --- Helper methods for deploy() ---

    def _validate_platform(self):
        """Make sure the local environment and project supports deployment to Coolify Self-hosted.

        Returns:
            None
        Raises:
            DSDCommandError: If we find any reason deployment won't work.
        """
        pass


    def _prep_automate_all(self):
        """Take any further actions needed if using automate_all."""
        pass


    def _conclude_automate_all(self):
        """Finish automating the push to Coolify Self-hosted.

        - Commit all changes.
        - Deploy to Coolify
        """
        # Making this check here lets deploy() be cleaner.
        if not dsd_config.automate_all:
            return

        plugin_utils.commit_changes()

        # Push project.
        plugin_utils.write_output("  Deploying to Coolify Self-hosted...")
        
        # For now, we'll just set a placeholder URL
        # In a real implementation, this would interact with Coolify's API
        self.deployed_url = "https://your-app.coolify.example.com"

    def _show_success_message(self):
        """After a successful run, show a message about what to do next.

        Describe ongoing approach of commit, push, migrate.
        """
        if dsd_config.automate_all:
            msg = platform_msgs.success_msg_automate_all(self.deployed_url)
        else:
            msg = platform_msgs.success_msg(log_output=dsd_config.log_output)
        plugin_utils.write_output(msg)
    
    def _add_dockerfile(self):
        """Add a Dockerfile optimized for Coolify deployment."""
        template_path = self.templates_path / "dockerfile_example"
        context = {
            "django_project_name": dsd_config.local_project_name,
        }
        contents = plugin_utils.get_template_string(template_path, context)

        # Write file to project.
        path = dsd_config.project_root / "Dockerfile"
        plugin_utils.add_file(path, contents)
    
    def _add_dockerignore(self):
        """Add a .dockerignore file to exclude unnecessary files."""
        dockerignore_content = """
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis
.DS_Store
*.sqlite3
db.sqlite3
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
node_modules/
.npm
.eslintcache
"""
        path = dsd_config.project_root / ".dockerignore"
        plugin_utils.add_file(path, dockerignore_content.strip())
    
    def _modify_settings(self):
        """Add Coolify-specific settings to Django settings."""
        template_path = self.templates_path / "settings.py"
        context = {
            "deployed_project_name": self._get_deployed_project_name(),
        }
        plugin_utils.modify_settings_file(template_path, context)
    
    def _add_requirements(self):
        """Add requirements needed for Coolify deployment."""
        requirements = [
            "gunicorn>=20.1.0",
            "psycopg2-binary>=2.9.0", 
            "dj-database-url>=1.0.0",
            "whitenoise>=6.0.0"
        ]
        plugin_utils.add_packages(requirements)
    
    def _get_deployed_project_name(self):
        """Get the name that will be used for the deployed project."""
        # Use the local project name as the base for the deployed name
        return dsd_config.local_project_name.lower().replace('_', '-')
