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

import sys, os, re, json, subprocess
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
        - Push to repository
        - Create application in Coolify (if automate_all)
        - Deploy to Coolify
        - Wait for deployment and show actual URL
        """
        # Making this check here lets deploy() be cleaner.
        if not dsd_config.automate_all:
            return

        plugin_utils.commit_changes()

        # Push changes to repository so Coolify can access them
        plugin_utils.write_output("  Pushing changes to repository...")
        self._push_to_repository()

        # Create application and deploy via Coolify API
        plugin_utils.write_output("  Deploying to Coolify Self-hosted...")
        
        app_uuid = self._create_coolify_application()
        if app_uuid:
            deployment_uuid = self._deploy_to_coolify(app_uuid)
            
            if deployment_uuid:
                # Wait for deployment to complete and get the actual URL
                app_url = self._wait_for_deployment(app_uuid, deployment_uuid)
                if app_url:
                    plugin_utils.write_output(f"  🚀 Deployment completed successfully!")
                    plugin_utils.write_output(f"  🌐 Your app is live at: {app_url}")
                    self.deployed_url = app_url
                else:
                    plugin_utils.write_output("  ⚠️  Deployment triggered but URL not available yet.")
            else:
                plugin_utils.write_output("  ⚠️  Application created but deployment may need manual trigger.")
        else:
            # Fallback to manual instructions
            plugin_utils.write_output("  Please create and deploy the application manually in Coolify.")
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
        deployment_requirements = [
            "gunicorn>=20.1.0",
            "psycopg2-binary>=2.9.0", 
            "dj-database-url>=1.0.0",
            "whitenoise>=6.0.0"
        ]
        
        # Check if this is a uv project
        pyproject_path = dsd_config.project_root / "pyproject.toml"
        uv_lock_path = dsd_config.project_root / "uv.lock"
        
        if pyproject_path.exists() and uv_lock_path.exists():
            # This is a uv project, add dependencies via uv
            plugin_utils.write_output("  Adding deployment dependencies via uv...")
            self._add_uv_dependencies(deployment_requirements)
        else:
            # Fallback to traditional requirements.txt approach
            plugin_utils.add_packages(deployment_requirements)

    def _add_uv_dependencies(self, requirements):
        """Add dependencies to a uv project."""
        import subprocess
        
        for requirement in requirements:
            package_name = requirement.split('>=')[0].split('==')[0]
            
            try:
                plugin_utils.write_output(f"  Adding {package_name}...")
                result = subprocess.run(
                    ["uv", "add", requirement],
                    cwd=dsd_config.project_root,
                    capture_output=True,
                    text=True,
                    check=True
                )
                plugin_utils.write_output(f"    ✅ Added {package_name}")
                
            except subprocess.CalledProcessError as e:
                plugin_utils.write_output(f"    ❌ Failed to add {package_name}: {e}")
                plugin_utils.write_output(f"    You may need to add {requirement} manually with: uv add {requirement}")
            except FileNotFoundError:
                plugin_utils.write_output(f"    ❌ 'uv' command not found. Please install uv.")
                # Fallback to requirements.txt approach
                plugin_utils.add_packages([requirement])
                
        # After adding dependencies, regenerate requirements.txt for Docker build
        self._regenerate_requirements_txt()
                
    def _regenerate_requirements_txt(self):
        """Regenerate requirements.txt after adding uv dependencies."""
        plugin_utils.write_output("  Regenerating requirements.txt with new dependencies...")
        
        try:
            result = subprocess.run(
                ["uv", "export", "--format", "requirements-txt"],
                cwd=dsd_config.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Write the updated requirements to requirements.txt
            requirements_path = dsd_config.project_root / "requirements.txt"
            plugin_utils.add_file(requirements_path, result.stdout)
            plugin_utils.write_output("    ✅ Updated requirements.txt with all dependencies")
            
        except subprocess.CalledProcessError as e:
            plugin_utils.write_output(f"    ❌ Failed to regenerate requirements.txt: {e}")
        except FileNotFoundError:
            plugin_utils.write_output("    ❌ 'uv' command not found for regenerating requirements.txt")
    
    def _get_deployed_project_name(self):
        """Get the name that will be used for the deployed project."""
        # Use the local project name as the base for the deployed name
        return dsd_config.local_project_name.lower().replace('_', '-')

    # --- Coolify API Integration ---

    def _get_coolify_config(self):
        """Get Coolify API configuration from environment or user input."""
        coolify_url = os.environ.get('COOLIFY_URL')
        coolify_token = os.environ.get('COOLIFY_TOKEN')
        
        if not coolify_url:
            plugin_utils.write_output("  Coolify URL not found in environment.")
            plugin_utils.write_output("  Please set COOLIFY_URL environment variable or provide it now.")
            coolify_url = input("  Enter your Coolify instance URL (e.g., https://coolify.example.com): ").strip()
            
        if not coolify_token:
            plugin_utils.write_output("  Coolify API token not found in environment.")
            plugin_utils.write_output("  Please set COOLIFY_TOKEN environment variable or provide it now.")
            plugin_utils.write_output("  You can create an API token in Coolify: Keys & Tokens > API tokens")
            coolify_token = input("  Enter your Coolify API token: ").strip()
        
        if not coolify_url or not coolify_token:
            raise DSDCommandError("Coolify URL and API token are required for automatic deployment.")
            
        # Ensure URL doesn't end with slash
        coolify_url = coolify_url.rstrip('/')
        
        return coolify_url, coolify_token

    def _make_coolify_request(self, method, endpoint, data=None):
        """Make a request to the Coolify API."""
        coolify_url, coolify_token = self._get_coolify_config()
        
        url = f"{coolify_url}/api/v1{endpoint}"
        headers = {
            'Authorization': f'Bearer {coolify_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise DSDCommandError(f"Failed to communicate with Coolify API: {e}")

    def _get_or_create_project(self):
        """Get existing project or create a new one."""
        project_name = self._get_deployed_project_name()
        
        try:
            # Try to list existing projects first
            projects = self._make_coolify_request('GET', '/projects')
            
            # Look for existing project with same name
            for project in projects:
                if project.get('name', '').lower() == project_name.lower():
                    plugin_utils.write_output(f"  Using existing project: {project['name']}")
                    return project['uuid']
            
            # Create new project if not found
            plugin_utils.write_output(f"  Creating new project: {project_name}")
            project_data = {
                'name': project_name,
                'description': f'Django project: {dsd_config.local_project_name}'
            }
            
            result = self._make_coolify_request('POST', '/projects', project_data)
            return result['uuid']
            
        except Exception as e:
            raise DSDCommandError(f"Failed to get or create project: {e}")

    def _get_server_info(self):
        """Get the first available server."""
        try:
            servers = self._make_coolify_request('GET', '/servers')
            
            if not servers:
                raise DSDCommandError("No servers found in your Coolify instance. Please add a server first.")
            
            # Use the first available server
            server = servers[0]
            plugin_utils.write_output(f"  Using server: {server['name']} ({server['ip']})")
            
            return {
                'server_uuid': server['uuid'],
                'environment_name': 'production',
                'environment_uuid': 'production',  # Coolify seems to use 'production' as default
                'destination_uuid': server['uuid']  # For standalone Docker, destination = server
            }
            
        except Exception as e:
            raise DSDCommandError(f"Failed to get server information: {e}")

    def _create_coolify_application(self):
        """Create application in Coolify via API."""
        if not dsd_config.automate_all:
            return None
            
        plugin_utils.write_output("  Creating application in Coolify...")
        
        try:
            # Get project and server info
            project_uuid = self._get_or_create_project()
            server_info = self._get_server_info()
            
            # Determine git repository URL
            # For now, we'll assume it's a public GitHub repo
            # In the future, this could be made more intelligent
            git_repo = f"https://github.com/{os.environ.get('GITHUB_REPOSITORY', 'user/repo')}"
            
            # Check if we can determine the git repository from the current directory
            try:
                result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                      capture_output=True, text=True, check=True)
                git_repo = result.stdout.strip()
                
                # Convert SSH to HTTPS for public repos
                if git_repo.startswith('git@github.com:'):
                    git_repo = git_repo.replace('git@github.com:', 'https://github.com/')
                    if git_repo.endswith('.git'):
                        git_repo = git_repo[:-4]
                        
            except subprocess.CalledProcessError:
                plugin_utils.write_output("  Warning: Could not determine git repository from current directory")
                git_repo = input("  Enter your git repository URL (e.g., https://github.com/user/repo): ").strip()
            
            # Create application payload
            application_data = {
                'project_uuid': project_uuid,
                'server_uuid': server_info['server_uuid'],
                'environment_name': server_info['environment_name'],
                'environment_uuid': server_info['environment_uuid'],
                'destination_uuid': server_info['destination_uuid'],
                'git_repository': git_repo,
                'git_branch': 'main',  # Could be made configurable
                'build_pack': 'dockerfile',  # We're providing a Dockerfile
                'ports_exposes': '8000',
                'name': self._get_deployed_project_name(),
                'description': f'Django application: {dsd_config.local_project_name}',
                'health_check_enabled': True,
                'health_check_path': '/',
            }
            
            plugin_utils.write_output(f"  Creating application for repository: {git_repo}")
            result = self._make_coolify_request('POST', '/applications/public', application_data)
            
            app_uuid = result.get('uuid')
            if app_uuid:
                plugin_utils.write_output(f"  ✅ Application created successfully!")
                plugin_utils.write_output(f"  Application UUID: {app_uuid}")
                return app_uuid
            else:
                raise DSDCommandError("Application created but no UUID returned")
                
        except Exception as e:
            plugin_utils.write_output(f"  ❌ Failed to create application in Coolify: {e}")
            plugin_utils.write_output("  You can create the application manually in the Coolify dashboard.")
            return None

    def _deploy_to_coolify(self, app_uuid):
        """Deploy the application in Coolify."""
        if not app_uuid:
            return None
            
        plugin_utils.write_output("  Triggering deployment in Coolify...")
        
        try:
            result = self._make_coolify_request('GET', f'/deploy?uuid={app_uuid}')
            
            deployment_uuid = None
            if 'deployments' in result and result['deployments']:
                deployment_uuid = result['deployments'][0].get('deployment_uuid')
                
            if deployment_uuid:
                plugin_utils.write_output(f"  ✅ Deployment started!")
                plugin_utils.write_output(f"  Deployment UUID: {deployment_uuid}")
                
                # Set the deployed URL for success message
                coolify_url, _ = self._get_coolify_config()
                self.deployed_url = f"{coolify_url}/project/{app_uuid}"
                
                return deployment_uuid
            else:
                plugin_utils.write_output("  ⚠️  Deployment request sent but no deployment UUID returned")
                return None
                
        except Exception as e:
            plugin_utils.write_output(f"  ❌ Failed to deploy application: {e}")
            plugin_utils.write_output("  You can deploy manually from the Coolify dashboard.")
            return None

    def _push_to_repository(self):
        """Push committed changes to the repository."""
        try:
            # Push to the current branch
            result = subprocess.run(
                ["git", "push"],
                cwd=dsd_config.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            plugin_utils.write_output("  ✅ Changes pushed to repository")
        except subprocess.CalledProcessError as e:
            plugin_utils.write_output(f"  ⚠️  Failed to push to repository: {e}")
            plugin_utils.write_output("  Please push manually: git push")

    def _wait_for_deployment(self, app_uuid, deployment_uuid):
        """Wait for deployment to complete and return the application URL."""
        import time
        
        plugin_utils.write_output("  ⏳ Waiting for deployment to complete...")
        
        max_wait_time = 300  # 5 minutes
        poll_interval = 10   # 10 seconds
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            try:
                # Check deployment status
                result = self._make_coolify_request('GET', f'/deployments?uuid={deployment_uuid}')
                
                if 'status' in result:
                    status = result['status']
                    
                    if status == 'finished':
                        # Try to get the application URL
                        app_result = self._make_coolify_request('GET', f'/applications?uuid={app_uuid}')
                        if 'fqdn' in app_result and app_result['fqdn']:
                            return f"https://{app_result['fqdn']}"
                        else:
                            # Fallback to Coolify dashboard URL
                            coolify_url, _ = self._get_coolify_config()
                            return f"{coolify_url}/project/{app_uuid}"
                    elif status == 'failed':
                        plugin_utils.write_output("  ❌ Deployment failed")
                        return None
                    else:
                        plugin_utils.write_output(f"  ⏳ Deployment status: {status}")
                
            except Exception as e:
                plugin_utils.write_output(f"  ⚠️  Error checking deployment status: {e}")
            
            time.sleep(poll_interval)
            elapsed_time += poll_interval
        
        plugin_utils.write_output("  ⏰ Deployment taking longer than expected")
        return None
