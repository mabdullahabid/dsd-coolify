"""A collection of messages used during the configuration and deployment process."""

# For conventions, see documentation in core deploy_messages.py

from textwrap import dedent

from django.conf import settings


confirm_automate_all = """
The --automate-all flag means django-simple-deploy will:
- Configure your project with the necessary files for Coolify deployment (Dockerfile, .dockerignore, requirements)
- Modify your settings.py to work with Coolify's environment
- Commit all changes to your project that are necessary for deployment
- Deploy your project to Coolify Self-hosted
- Open your deployed project in a new browser tab
"""

cancel_coolifyselfhosted = """
Okay, cancelling Coolify Self-hosted configuration and deployment.
"""

# DEV: This could be moved to deploy_messages, with an arg for platform and URL.
cli_not_installed = """
In order to deploy to Coolify Self-hosted, you need to install the Coolify Self-hosted CLI.
  See here: ...
After installing the CLI, you can run the deploy command again.
"""

cli_logged_out = """
You are currently logged out of the Coolify Self-hosted CLI. Please log in,
  and then run the deploy command again.
You can log in from  the command line:
  $ ...
"""


# --- Dynamic strings ---
# These need to be generated in functions, to display information that's determined as
# the script runs.

def success_msg(log_output=""):
    """Success message, for configuration-only run.

    Note: This is immensely helpful; I use it just about every time I do a
      manual test run.
    """

    msg = dedent(
        f"""
        --- Your project is now configured for deployment on Coolify Self-hosted ---

        To deploy your project, you will need to:
        - Commit the changes made in the configuration process:
            $ git status
            $ git add .
            $ git commit -am "Configured project for Coolify deployment."
        - Push your project to your Git repository
        - In your Coolify dashboard:
            1. Create a new application
            2. Connect it to your Git repository
            3. Coolify will automatically detect the Dockerfile and deploy your app
        - Set up environment variables in Coolify:
            - SECRET_KEY: A secure Django secret key
            - DATABASE_URL: Your PostgreSQL database URL (if using external DB)
            - DEBUG: false (for production)
        - As you develop your project further:
            - Make local changes
            - Commit your local changes  
            - Push to your repository - Coolify will automatically redeploy
    """
    )

    if log_output:
        msg += dedent(
            f"""
        - You can find a full record of this configuration in the dsd_logs directory.
        """
        )

    return msg


def success_msg_automate_all(deployed_url):
    """Success message, when using --automate-all."""

    msg = dedent(
        f"""

        --- Your project should now be deployed on Coolify Self-hosted ---

        Your Django application has been configured and committed to Git.
        - You can visit your project at {deployed_url}
        - The following files were added/modified:
            * Dockerfile - Container configuration for your Django app
            * .dockerignore - Files to exclude from the container
            * requirements.txt - Updated with deployment dependencies
            * settings.py - Modified with production settings

        Next steps:
        1. Push your changes to your Git repository
        2. In Coolify, create a new application and connect it to your repository
        3. Set environment variables (SECRET_KEY, DATABASE_URL, etc.)
        4. Coolify will build and deploy your application automatically

        For future deployments, just push changes to your repository!
    """
    )
    return msg
