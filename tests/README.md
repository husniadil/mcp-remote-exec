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

**Current Status:** 290 tests, 61% overall coverage

### Config Layer (100% coverage)

- ✅ `HostConfig` dataclass - authentication methods, configuration validation
- ✅ `SecurityConfig` dataclass - security settings, limits, host key checking
- ✅ `SSHConfig` class - initialization, validation, environment variable handling
- ✅ Constants and exceptions - complete coverage

### Data Access Layer

#### High Coverage (95%+):

- ✅ `SSHConnectionManager` (98% coverage) - 32 comprehensive tests
  - SSH key loading (RSA, Ed25519, ECDSA)
  - Connection creation and management
  - Password and key authentication
  - Command execution with timeouts
  - Error handling and cleanup
  - Context manager support
- ✅ `PathValidator` (100% coverage) - path validation, traversal prevention
- ✅ Exceptions (100% coverage) - all exception types

#### Needs Improvement:

- ⚠️ `SFTPManager` (22% coverage) - basic tests only, needs upload/download testing

### Services Layer

#### High Coverage:

- ✅ `OutputFormatter` (98% coverage) - text/JSON formatting, truncation, error handling
- ✅ Command output formatting - success/failure/timeout scenarios
- ✅ File transfer result formatting - upload/download operations

#### Moderate Coverage:

- ⚠️ `CommandService` (38% coverage) - basic delegation tests, needs integration tests
- ⚠️ `FileTransferService` (29% coverage) - basic delegation tests, needs integration tests

### Presentation Layer

#### High Coverage:

- ✅ Models (100% coverage) - all input validation models
- ✅ Service Container (100% coverage) - dependency injection
- ✅ Validators (100% coverage) - permission validation
- ✅ Bootstrap (71% coverage) - initialization and wiring

#### Needs Improvement:

- ⚠️ MCP Tools (0% coverage) - tool registration not tested
- ❌ Main CLI (0% coverage) - entry point not tested (less critical)

### Plugin System

#### High Coverage:

- ✅ All plugin configs (100% coverage)
- ✅ All plugin models (100% coverage)
- ✅ All plugin constants (100% coverage)
- ✅ ImageKit transfer manager (100% coverage)
- ✅ Plugin base interface (79% coverage)

#### Moderate Coverage:

- ⚠️ Proxmox service (46% coverage) - core functionality tested
- ⚠️ ImageKit service (43% coverage) - core functionality tested
- ⚠️ ImageKit client (37% coverage) - basic operations tested
- ⚠️ Proxmox tools (38% coverage) - tool registration tested
- ⚠️ Registry (23% coverage) - basic registration tested

#### Needs Improvement:

- ⚠️ ImageKit tools (16% coverage) - tool registration needs more tests

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

Priority areas for additional test coverage:

### High Priority

- **SFTP Manager** (22% → 80%+) - Add upload/download operation tests with paramiko mocking
- **Command Service** (38% → 80%+) - Add integration tests with SSH connection manager
- **File Transfer Service** (29% → 80%+) - Add integration tests with SFTP manager
- **Plugin Registry** (23% → 80%+) - Add plugin coordination and conflict tests

### Medium Priority

- **MCP Tools** (0% → 50%+) - Add tool registration and error handling tests
- **ImageKit Tools** (16% → 60%+) - Add two-phase transfer workflow tests
- **Proxmox Tools** (38% → 60%+) - Add container operation tests
- **Bootstrap** (71% → 90%+) - Add conditional tool registration edge cases

### Low Priority

- **ImageKit/Proxmox Services** (43%/46% → 70%+) - Add edge case and error scenario tests
- **ImageKit Client** (37% → 70%+) - Add ImageKit API interaction tests
- **Main CLI** (0% → 40%+) - Add CLI argument parsing tests (less critical for MCP server)

### Completed ✅

- ~~SSH connection management~~ - **DONE** (98% coverage, 32 comprehensive tests)
- ~~Path validation~~ - **DONE** (100% coverage, removed deprecated code)

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
