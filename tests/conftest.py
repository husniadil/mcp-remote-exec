"""Pytest configuration and fixtures"""

import os
import pytest
from unittest.mock import MagicMock, patch
from mcp_remote_exec.config.ssh_config import SSHConfig, HostConfig, SecurityConfig


@pytest.fixture
def mock_env_minimal():
    """Minimal environment variables for testing"""
    return {
        "I_ACCEPT_RISKS": "true",
        "HOST": "test.example.com",
        "SSH_USERNAME": "testuser",
        "SSH_PASSWORD": "testpass",
    }


@pytest.fixture
def mock_env_with_key(tmp_path):
    """Environment variables with SSH key"""
    key_file = tmp_path / "test_key"
    key_file.write_text("fake ssh key")

    return {
        "I_ACCEPT_RISKS": "true",
        "HOST": "test.example.com",
        "SSH_USERNAME": "testuser",
        "SSH_KEY": str(key_file),
    }


@pytest.fixture
def mock_host_config():
    """Create a mock HostConfig for testing"""
    return HostConfig(
        name="test",
        host="test.example.com",
        port=22,
        username="testuser",
        password="testpass",
    )


@pytest.fixture
def mock_security_config():
    """Create a mock SecurityConfig for testing"""
    return SecurityConfig(
        accept_risks=True,
        character_limit=25000,
        max_file_size=10485760,
        default_timeout=30,
        max_timeout=300,
        strict_host_key_checking=True,
    )


@pytest.fixture
def mock_ssh_config(mock_host_config, mock_security_config):
    """Create a mock SSHConfig for testing"""
    config = MagicMock(spec=SSHConfig)
    config.host = mock_host_config
    config.security = mock_security_config
    return config
