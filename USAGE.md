# DSD Coolify Plugin Usage

A django-simple-deploy plugin for deploying Django applications to Coolify Self-hosted with automatic API integration.

## Features

🚀 **One-Command Deployment**: Deploy your Django app with just `python manage.py deploy --automate-all`

🔄 **uv Project Support**: Automatically generates `requirements.txt` from your `pyproject.toml` and `uv.lock`

🤖 **API Integration**: Automatically creates applications and triggers deployments via Coolify's API

📦 **Complete Configuration**: Generates Dockerfile, .dockerignore, and production settings

## Quick Start

### 1. Install the Plugin

Add the plugin as an editable dependency to your Django project:

```bash
uv add --editable /path/to/dsd-coolify
```

### 2. Add to Django Settings

Add `django_simple_deploy` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... your other apps
    'django_simple_deploy',
]
```

### 3. Basic Deployment (Manual)

Configure your project for Coolify deployment:

```bash
python manage.py deploy
```

This will:
- Auto-generate `requirements.txt` from uv projects
- Create a production-ready `Dockerfile`
- Add `.dockerignore` file
- Configure production settings
- Show manual deployment instructions

### 4. Automatic Deployment (Recommended)

For fully automated deployment with API integration:

#### Set Environment Variables

```bash
export COOLIFY_URL="https://your-coolify-instance.com"
export COOLIFY_TOKEN="your-api-token"
```

**To get your API token:**
1. Go to your Coolify dashboard
2. Navigate to **Keys & Tokens** > **API tokens**
3. Create a new token

#### Deploy Automatically

```bash
python manage.py deploy --automate-all
```

This will automatically:
- Configure your project files
- Create a new project in Coolify (if needed)
- Create the application via API
- Trigger the initial deployment
- Commit all changes to git

## Configuration Options

### Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `COOLIFY_URL` | Your Coolify instance URL | Yes (for auto) | `https://coolify.example.com` |
| `COOLIFY_TOKEN` | API token from Coolify | Yes (for auto) | `your-api-token-here` |
| `GITHUB_REPOSITORY` | GitHub repo (auto-detected) | No | `user/repo` |

### Git Repository Detection

The plugin automatically detects your git repository from:
1. Current git remote origin
2. `GITHUB_REPOSITORY` environment variable
3. Manual input prompt (if auto-detection fails)

## Manual Deployment Steps

If you prefer manual deployment or if automatic deployment fails:

1. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Configure for Coolify deployment"
   git push
   ```

2. **Create application in Coolify:**
   - Go to your Coolify dashboard
   - Create a new application
   - Connect it to your git repository
   - Coolify will auto-detect the Dockerfile

3. **Set environment variables in Coolify:**
   - `SECRET_KEY`: Django secret key
   - `DATABASE_URL`: PostgreSQL connection string (if using external DB)
   - `DEBUG`: `false` for production

## Project Structure

After running the deploy command, your project will have:

```
your-project/
├── Dockerfile              # Optimized for Django + Coolify
├── .dockerignore           # Excludes unnecessary files
├── requirements.txt        # Auto-generated from uv projects
├── hello_django/
│   └── settings.py         # Updated with production settings
└── dsd_logs/              # Deployment logs
```

## Features for uv Users

This plugin has **first-class support** for uv projects with intelligent dependency management:

### Automatic Detection & Integration
- **Auto-detection**: Detects `pyproject.toml` + `uv.lock` combination
- **Smart dependency management**: Adds deployment dependencies via `uv add` (not just requirements.txt)
- **Proper environment sync**: Dependencies are available in your uv environment immediately
- **Docker compatibility**: Auto-regenerates `requirements.txt` for Docker builds

### How it works
1. **Detects uv project**: Checks for `pyproject.toml` and `uv.lock`
2. **Adds dependencies properly**: Uses `uv add gunicorn psycopg2-binary dj-database-url whitenoise`
3. **Updates lock file**: Your `uv.lock` is updated with deployment dependencies
4. **Regenerates requirements.txt**: Creates Docker-compatible requirements file
5. **Seamless experience**: All dependencies available in both uv environment and Docker

### Before and After

**Before deployment:**
```toml
# pyproject.toml
dependencies = [
    "django>=5.2.5",
    "django-simple-deploy>=1.0.0",
]
```

**After deployment:**
```toml
# pyproject.toml  
dependencies = [
    "dj-database-url>=1.0.0",
    "django>=5.2.5", 
    "django-simple-deploy>=1.0.0",
    "gunicorn>=20.1.0",
    "psycopg2-binary>=2.9.0",
    "whitenoise>=6.0.0",
]
```

Plus properly updated `uv.lock` and `requirements.txt` files!

### No Manual Steps Required
- ❌ No need to manually run `uv add` commands
- ❌ No need to manually generate `requirements.txt` 
- ❌ No dependency availability issues
- ✅ Everything handled automatically

## Troubleshooting

### API Token Issues
- Make sure your token has the right permissions
- Verify the token in Coolify dashboard under Keys & Tokens

### Git Repository Detection
- Ensure you have a git remote origin set
- For private repos, you'll need to set up SSH keys or GitHub app in Coolify

### uv Project Issues
- **Dependencies not found**: If deployment dependencies aren't available, check that `uv add` completed successfully
- **Lock file conflicts**: If you have merge conflicts in `uv.lock`, resolve them and re-run the deploy command
- **Requirements.txt outdated**: The plugin auto-regenerates this file, so don't edit it manually

### Build Failures
- Check that your `requirements.txt` includes all dependencies
- Verify your `Dockerfile` settings
- Check Coolify deployment logs for specific errors

## Advanced Usage

### Custom Git Branch
The plugin uses `main` branch by default. For different branches, you can modify the plugin or set this up manually in Coolify.

### Custom Dockerfile
The generated Dockerfile is optimized for most Django projects. You can customize it after generation if needed.

### Multiple Environments
For staging/production environments, create separate projects in Coolify and use different API tokens or configurations.

## Support

- Plugin Issues: Create issues in the plugin repository
- Coolify Issues: Check [Coolify documentation](https://coolify.io/docs)
- Django Simple Deploy: See [django-simple-deploy docs](https://django-simple-deploy.readthedocs.io)
