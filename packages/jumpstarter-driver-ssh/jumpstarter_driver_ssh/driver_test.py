import tempfile
from pathlib import Path

import pytest

from .driver import SshNetwork
from jumpstarter.common.utils import serve

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


class TestSshNetwork:
    """Test SSH Network driver functionality."""

    def test_driver_initialization_password_auth(self):
        """Test driver initialization with password authentication."""
        config = {
            "host": "test.example.com",
            "username": "testuser",
            "password": "testpass"
        }

        driver = SshNetwork(**config)
        assert driver.host == "test.example.com"
        assert driver.username == "testuser"
        assert driver.password == "testpass"
        assert driver.port == 22  # default port

    def test_driver_initialization_key_auth(self):
        """Test driver initialization with private key authentication."""
        # Create a temporary key file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
            f.write("-----BEGIN PRIVATE KEY-----\ntest_key_content\n-----END PRIVATE KEY-----")
            key_path = f.name

        try:
            config = {
                "host": "test.example.com",
                "username": "testuser",
                "private_key_path": key_path
            }

            driver = SshNetwork(**config)
            assert driver.host == "test.example.com"
            assert driver.username == "testuser"
            assert driver.private_key_path == key_path
        finally:
            Path(key_path).unlink()

    def test_driver_initialization_missing_auth(self):
        """Test driver initialization fails without authentication."""
        config = {
            "host": "test.example.com",
            "username": "testuser"
            # Missing both password and private_key_path
        }

        with pytest.raises(ValueError, match="Either password or private_key_path must be provided"):
            SshNetwork(**config)

    def test_driver_initialization_missing_key_file(self):
        """Test driver initialization fails with non-existent key file."""
        config = {
            "host": "test.example.com",
            "username": "testuser",
            "private_key_path": "/non/existent/key.pem"
        }

        with pytest.raises(FileNotFoundError):
            SshNetwork(**config)

    def test_client_class_reference(self):
        """Test that driver references correct client class."""
        assert SshNetwork.client() == "jumpstarter_driver_ssh.client.SshNetworkClient"

    def test_close_connection(self):
        """Test connection closing."""
        driver = SshNetwork(
            host="test.example.com",
            username="testuser",
            password="testpass"
        )

        # Should not raise an exception when no connection exists
        driver.close()

    def test_driver_configuration_defaults(self):
        """Test driver default configuration values."""
        driver = SshNetwork(
            host="test.example.com",
            username="testuser",
            password="testpass"
        )

        assert driver.port == 22
        assert driver.host_key_checking is True
        assert driver.connect_timeout == 30
        assert driver.keepalive_interval == 30
        assert driver.private_key_passphrase is None

    def test_driver_configuration_custom(self):
        """Test driver with custom configuration values."""
        driver = SshNetwork(
            host="test.example.com",
            port=2222,
            username="testuser",
            password="testpass",
            host_key_checking=False,
            connect_timeout=60,
            keepalive_interval=120
        )

        assert driver.port == 2222
        assert driver.host_key_checking is False
        assert driver.connect_timeout == 60
        assert driver.keepalive_interval == 120


async def test_driver_with_serve():
    """Test driver integration using serve utility."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
        f.write("-----BEGIN PRIVATE KEY-----\ntest_key_content\n-----END PRIVATE KEY-----")
        key_path = f.name

    try:
        instance = SshNetwork(
            host="test.example.com",
            username="testuser",
            private_key_path=key_path
        )

        with serve(instance) as client:
            # Test that we can call the client methods
            assert hasattr(client, 'execute')
            assert hasattr(client, 'test_connection')
            assert hasattr(client, 'upload_file')
            assert hasattr(client, 'download_file')
            assert hasattr(client, 'run_script')

            # Test client class
            assert client.__class__.__name__ == "SshNetworkClient"
    finally:
        Path(key_path).unlink()
