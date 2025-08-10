"""Integration tests for django-simple-deploy, targeting Fly.io."""

import sys
from pathlib import Path
import subprocess

import pytest

from tests.integration_tests.utils import it_helper_functions as hf
from tests.integration_tests.conftest import (
    tmp_project,
    run_dsd,
    reset_test_project,
    pkg_manager,
    dsd_version,
)


# --- Fixtures ---


# --- Test modifications to project files. ---


def test_settings(tmp_project):
    """Verify there's a Coolify Self-hosted-specific settings section.
    This function only checks the entire settings file. It does not examine
      individual settings.

    Note: This will fail as soon as you make updates to the user's settings file.
    That's good! Look in the test's temp dir, look at the settings file after it was
    modified, and if it's correct, copy that file to reference_files. Tests should pass
    again.
    """
    hf.check_reference_file(tmp_project, "blog/settings.py", "dsd-coolify")


def test_requirements_txt(tmp_project, pkg_manager, tmp_path, dsd_version):
    """Test that the requirements.txt file is correct.
    Note: This will fail as soon as you add new requirements. That's good! Look in the
    test's temp dir, look at the requirements.txt file after it was modified, and if
    it's correct, copy it to reference files. Tests should pass again.
    """
    if pkg_manager == "req_txt":
        context = {"current-version": dsd_version}
        hf.check_reference_file(
            tmp_project,
            "requirements.txt",
            "dsd-coolify",
            context=context,
            tmp_path=tmp_path,
        )
    elif pkg_manager in ["poetry", "pipenv"]:
        assert not Path("requirements.txt").exists()


def test_pyproject_toml(tmp_project, pkg_manager, tmp_path, dsd_version):
    """Test that pyproject.toml is correct."""
    if pkg_manager in ("req_txt", "pipenv"):
        assert not Path("pyproject.toml").exists()
    elif pkg_manager == "poetry":
        context = {"current-version": dsd_version}
        hf.check_reference_file(
            tmp_project,
            "pyproject.toml",
            "dsd-coolify",
            context=context,
            tmp_path=tmp_path,
        )


def test_pipfile(tmp_project, pkg_manager, tmp_path, dsd_version):
    """Test that Pipfile is correct."""
    if pkg_manager in ("req_txt", "poetry"):
        assert not Path("Pipfile").exists()
    elif pkg_manager == "pipenv":
        context = {"current-version": dsd_version}
        hf.check_reference_file(
            tmp_project, "Pipfile", "dsd-coolify", context=context, tmp_path=tmp_path
        )


def test_gitignore(tmp_project):
    """Test that .gitignore has been modified correctly."""
    hf.check_reference_file(tmp_project, ".gitignore", "dsd-coolify")


# --- Test Coolify Self-hosted-specific files ---

# Example test for a platform-specicific file such as Fly's Dockerfile
# def test_creates_dockerfile(tmp_project, pkg_manager):
#     """Verify that dockerfile is created correctly."""
#     if pkg_manager == "req_txt":
#         hf.check_reference_file(tmp_project, "dockerfile", "dsd-flyio")
#     elif pkg_manager == "poetry":
#         hf.check_reference_file(
#             tmp_project,
#             "dockerfile",
#             "dsd-flyio",
#             reference_filename="poetry.dockerfile",
#         )
#     elif pkg_manager == "pipenv":
#         hf.check_reference_file(
#             tmp_project,
#             "dockerfile",
#             "dsd-flyio",
#             reference_filename="pipenv.dockerfile",
#         )


# --- Test logs ---


def test_log_dir(tmp_project):
    """Test that the log directory exists, and contains an appropriate log file."""
    log_path = Path(tmp_project / "dsd_logs")
    assert log_path.exists()

    # There should be exactly two log files.
    log_files = sorted(log_path.glob("*"))
    log_filenames = [lf.name for lf in log_files]
    # Check for exactly the log files we expect to find.
    # DEV: Currently just testing that a log file exists. Add a regex text for a file
    # like "simple_deploy_2022-07-09174245.log".
    assert len(log_files) == 1

    # Read log file. We can never just examine the log file directly to a reference,
    #   because it will have different timestamps.
    # If we need to, we can make a comparison of all content except timestamps.
    # DEV: Look for specific log file; not sure this log file is always the second one.
    #   We're looking for one similar to "simple_deploy_2022-07-09174245.log".
    log_file = log_files[0]  # update on friendly summary
    log_file_text = log_file.read_text()

    # DEV: Update these for more platform-specific log messages.
    # Spot check for opening log messages.
    assert "INFO: Logging run of `manage.py deploy`..." in log_file_text
    assert "INFO: Configuring project for deployment to Coolify Self-hosted..." in log_file_text

    assert "INFO: CLI args:" in log_file_text
    assert (
        "INFO: Deployment target: Coolify Self-hosted" in log_file_text
        or "INFO: Deployment target: Coolify Self-hosted" in log_file_text
    )
    assert "INFO:   Using plugin: dsd_coolify" in log_file_text
    assert "INFO: Local project name: blog" in log_file_text
    assert "INFO: git status --porcelain" in log_file_text
    assert "INFO: ?? dsd_logs/" in log_file_text

    # Spot check for success messages.
    assert (
        "INFO: --- Your project is now configured for deployment on Coolify Self-hosted ---"
        in log_file_text
    )
    assert "INFO: To deploy your project, you will need to:" in log_file_text

    assert (
        "INFO: - You can find a full record of this configuration in the dsd_logs directory."
        in log_file_text
    )
