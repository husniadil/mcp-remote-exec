# Test Suite for mcp-remote-exec

This directory contains comprehensive unit tests for the mcp-remote-exec project.

## Test Structure

```
tests/
├── config/              # Configuration layer tests
│   └── test_ssh_config.py
├── data_access/         # Data access layer tests
│   └── test_exceptions.py
├── services/            # Services layer tests
│   └── test_output_formatter.py
├── conftest.py          # Pytest fixtures and configuration
└── README.md           # This file
```

## Running Tests

### Run all tests
```bash
uv run pytest tests/ -v
```

### Run tests with coverage
```bash
uv run pytest tests/ -v --cov=src/mcp_remote_exec --cov-report=term-missing --cov-report=html
```

### Run specific test file
```bash
uv run pytest tests/config/test_ssh_config.py -v
```

### Run specific test class or function
```bash
uv run pytest tests/config/test_ssh_config.py::TestSSHConfig::test_init_with_password_auth -v
```

### Using taskipy shortcuts
```bash
uv run task test         # Run all tests
uv run task test-cov     # Run tests with coverage report
```

## Test Coverage

Current test coverage focuses on:

### Config Layer (100% coverage)
- `HostConfig` dataclass - authentication methods, configuration validation
- `SecurityConfig` dataclass - security settings, limits, host key checking
- `SSHConfig` class - initialization, validation, environment variable handling

### Data Access Layer (100% coverage for exceptions)
- `SSHConnectionError` - basic connection errors
- `AuthenticationError` - SSH authentication failures
- `CommandExecutionError` - command execution failures
- `SFTPError` - file transfer errors
- `FileValidationError` - file validation errors

### Services Layer (98% coverage for output_formatter)
- `FormattedResult` dataclass - result formatting with metadata
- `OutputFormatter` class - text/JSON formatting, truncation, error handling
- Command output formatting - success/failure/timeout scenarios
- File transfer result formatting - upload/download operations
- Summary statistics generation

## Test Fixtures

Common fixtures available in `conftest.py`:

- `mock_env_minimal` - Minimal environment variables for testing
- `mock_env_with_key` - Environment with SSH key authentication
- `mock_host_config` - Mock HostConfig instance
- `mock_security_config` - Mock SecurityConfig instance
- `mock_ssh_config` - Mock SSHConfig instance

## Writing New Tests

### Test Naming Convention
- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Example Test
```python
import pytest
from mcp_remote_exec.config.ssh_config import SSHConfig

def test_ssh_config_initialization(mock_env_minimal):
    """Test SSHConfig initialization with minimal config"""
    with patch.dict(os.environ, mock_env_minimal, clear=True):
        config = SSHConfig()
        assert config.host.host == "test.example.com"
```

## Future Test Additions

Areas that could benefit from additional tests:
- SSH connection management (requires paramiko mocking)
- SFTP operations (requires paramiko mocking)
- Command and file transfer services
- MCP tools and presentation layer
- Plugin system (base, registry)
- ImageKit plugin integration
- Proxmox plugin integration

## CI/CD Integration

These tests are designed to run in CI/CD pipelines:
- Fast execution (< 2 seconds for all tests)
- No external dependencies required
- Environment-based configuration via fixtures
- Clear pass/fail reporting

## Test Markers

Available pytest markers:
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests (future)
- `@pytest.mark.slow` - Slow tests (future)

Use markers to run specific test categories:
```bash
pytest -m unit          # Run only unit tests
pytest -m "not slow"    # Skip slow tests
```
