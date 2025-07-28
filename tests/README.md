# TUI Testing Guide

This directory contains comprehensive tests for both the Loguru TUI and Dynaconf TUI implementations in the fastapi-clean-example project. The tests are organized following hexagonal architecture principles and cover unit, integration, end-to-end, performance, and accessibility testing.

## 📁 Test Structure

```
tests/
├── __init__.py
├── conftest.py                    # Global test configuration and fixtures
├── README.md                      # This file
├── fixtures/                      # Test fixtures and utilities
│   ├── __init__.py
│   ├── tui_fixtures.py           # Common TUI test fixtures
│   └── mock_repositories.py      # Mock repository implementations
├── utils/                         # Test utilities and helpers
│   ├── __init__.py
│   └── tui_test_helpers.py       # TUI testing utilities
├── unit/                          # Unit tests
│   └── presentation/
│       ├── __init__.py
│       ├── test_loguru_tui.py    # Loguru TUI unit tests
│       └── test_dynaconf_tui.py  # Dynaconf TUI unit tests
├── integration/                   # Integration tests
│   └── test_tui_workflows.py     # Cross-layer integration tests
├── e2e/                          # End-to-end tests
│   └── test_complete_tui_flows.py # Complete user workflow tests
├── performance/                   # Performance tests
│   ├── __init__.py
│   └── test_tui_performance.py   # TUI performance tests
└── accessibility/                 # Accessibility tests
    ├── __init__.py
    └── test_tui_accessibility.py # TUI accessibility tests
```

## 🧪 Test Categories

### Unit Tests (`tests/unit/presentation/`)

Test individual TUI components in isolation:

- **Loguru TUI Tests** (`test_loguru_tui.py`):
  - App initialization and configuration
  - Navigation and user interactions
  - Configuration loading, saving, and testing
  - Error handling and edge cases
  - Performance characteristics

- **Dynaconf TUI Tests** (`test_dynaconf_tui.py`):
  - TUI component functionality
  - Form interactions and validation
  - Navigation and screen management
  - Data binding between TUI and domain models
  - Error handling and recovery

### Integration Tests (`tests/integration/`)

Test interactions between TUI and other architectural layers:

- **TUI Workflows** (`test_tui_workflows.py`):
  - Complete configuration lifecycle workflows
  - Cross-layer communication testing
  - Error propagation across layers
  - Concurrent operations handling
  - Data consistency verification

### End-to-End Tests (`tests/e2e/`)

Test complete user workflows from start to finish:

- **Complete TUI Flows** (`test_complete_tui_flows.py`):
  - Full configuration creation and usage workflows
  - Import/export functionality
  - Backup and recovery scenarios
  - Multi-configuration management
  - Cross-system integration
  - Error recovery workflows

### Performance Tests (`tests/performance/`)

Test performance characteristics and scalability:

- **TUI Performance** (`test_tui_performance.py`):
  - Configuration loading and saving performance
  - Preview generation performance
  - Memory usage characteristics
  - Concurrent operation performance
  - Scalability with large datasets

### Accessibility Tests (`tests/accessibility/`)

Test accessibility features and compliance:

- **TUI Accessibility** (`test_tui_accessibility.py`):
  - Keyboard navigation support
  - Screen reader compatibility
  - Focus management
  - Color and contrast accessibility
  - Text readability features
  - Responsive design for different terminal sizes

## 🔧 Test Fixtures and Utilities

### Fixtures (`tests/fixtures/`)

- **`tui_fixtures.py`**: Common fixtures for TUI testing including:
  - Sample logger configurations
  - Mock ports and adapters
  - Test data generators
  - Async test utilities

- **`mock_repositories.py`**: Mock implementations of repositories:
  - `MockLoggerConfigurationRepository`
  - `MockLoggerApplicationAdapter`
  - File system operation mocks

### Utilities (`tests/utils/`)

- **`tui_test_helpers.py`**: Helper classes and functions:
  - `TUITestHelper`: TUI interaction simulation
  - `ConfigurationTestHelper`: Configuration data management
  - `AsyncTestHelper`: Async operation utilities
  - `FileSystemTestHelper`: File system testing utilities

## 🚀 Running Tests

### Prerequisites

Install test dependencies:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Or using hatch
hatch env create dev
hatch shell dev
```

### Running All Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run with verbose output
pytest -v
```

### Running Specific Test Categories

```bash
# Run only unit tests
pytest tests/unit/

# Run only TUI tests
pytest -m tui

# Run only integration tests
pytest -m integration

# Run only end-to-end tests
pytest -m e2e

# Run only performance tests (slow)
pytest -m slow

# Skip slow tests
pytest -m "not slow"
```

### Running Specific Test Files

```bash
# Run Loguru TUI tests
pytest tests/unit/presentation/test_loguru_tui.py

# Run Dynaconf TUI tests
pytest tests/unit/presentation/test_dynaconf_tui.py

# Run integration tests
pytest tests/integration/test_tui_workflows.py

# Run performance tests
pytest tests/performance/test_tui_performance.py
```

### Running Tests with Specific Markers

```bash
# Run accessibility tests
pytest tests/accessibility/

# Run tests for specific components
pytest -k "loguru"
pytest -k "dynaconf"

# Run tests with timeout
pytest --timeout=30
```

## 🎯 Test Markers

The following pytest markers are available:

- `@pytest.mark.tui`: TUI-specific tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.e2e`: End-to-end tests
- `@pytest.mark.slow`: Slow-running tests (performance, large datasets)
- `@pytest.mark.asyncio`: Async tests

## 🔍 Test Configuration

### Environment Variables

The test suite automatically sets up TUI-friendly environment variables:

- `TERM=dumb`: Disable terminal features that interfere with testing
- `NO_COLOR=1`: Disable color output
- `TEXTUAL_HEADLESS=1`: Run Textual in headless mode

### Timeouts

- Default async test timeout: 10 seconds
- Performance test timeout: 30 seconds
- E2E test timeout: 60 seconds

### Test Data

Test data is generated using factories and fixtures to ensure:
- Consistent test data across test runs
- Isolation between tests
- Realistic data scenarios

## 📊 Coverage Goals

Target coverage levels:

- **Unit Tests**: 95%+ coverage of presentation layer components
- **Integration Tests**: 90%+ coverage of cross-layer interactions
- **E2E Tests**: 85%+ coverage of complete user workflows
- **Overall**: 90%+ total coverage

## 🐛 Debugging Tests

### Common Issues and Solutions

1. **TUI Tests Hanging**:
   ```bash
   # Run with timeout
   pytest --timeout=10 tests/unit/presentation/
   ```

2. **Async Test Issues**:
   ```bash
   # Check async fixtures and event loop setup
   pytest -v -s tests/unit/presentation/test_loguru_tui.py::TestLoguruConfigApp::test_load_configuration_success
   ```

3. **Mock Issues**:
   ```bash
   # Run with detailed mock information
   pytest -v -s --tb=long
   ```

### Debug Mode

```bash
# Run tests in debug mode
pytest --pdb

# Run with print statements visible
pytest -s

# Run with detailed traceback
pytest --tb=long
```

## 📝 Writing New Tests

### Test Naming Conventions

- Test files: `test_<component>_<type>.py`
- Test classes: `Test<ComponentName><TestType>`
- Test methods: `test_<functionality>_<scenario>`

### Example Test Structure

```python
"""Tests for new TUI component."""

import pytest
from unittest.mock import Mock, AsyncMock

from tests.fixtures.tui_fixtures import sample_logger_config
from tests.utils.tui_test_helpers import TUITestHelper

class TestNewTUIComponent:
    """Test new TUI component functionality."""
    
    @pytest.fixture
    def mock_component(self):
        """Create mock component for testing."""
        return Mock()
    
    @pytest.mark.asyncio
    async def test_component_functionality(self, mock_component):
        """Test component functionality."""
        # Arrange
        expected_result = "expected"
        mock_component.method.return_value = expected_result
        
        # Act
        result = await mock_component.method()
        
        # Assert
        assert result == expected_result
        mock_component.method.assert_called_once()
```

### Best Practices

1. **Use Descriptive Test Names**: Test names should clearly describe what is being tested
2. **Follow AAA Pattern**: Arrange, Act, Assert
3. **Use Appropriate Fixtures**: Leverage existing fixtures and create new ones as needed
4. **Mock External Dependencies**: Isolate the component under test
5. **Test Error Conditions**: Include negative test cases
6. **Use Async Properly**: Use `@pytest.mark.asyncio` for async tests
7. **Add Performance Considerations**: Consider adding performance tests for critical paths

## 🔄 Continuous Integration

### GitHub Actions

The test suite is configured to run in GitHub Actions with:

- Multiple Python versions (3.8, 3.9, 3.10, 3.11)
- Headless TUI testing environment
- Coverage reporting
- Performance regression detection

### Pre-commit Hooks

Tests are run as part of pre-commit hooks:

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## 📚 Additional Resources

- [Textual Testing Documentation](https://textual.textualize.io/guide/testing/)
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [Hexagonal Architecture Testing Patterns](https://alistair.cockburn.us/hexagonal-architecture/)

## 🤝 Contributing

When adding new TUI functionality:

1. **Add Unit Tests**: Test the component in isolation
2. **Add Integration Tests**: Test interactions with other layers
3. **Add E2E Tests**: Test complete user workflows
4. **Consider Performance**: Add performance tests for critical operations
5. **Check Accessibility**: Ensure accessibility features are tested
6. **Update Documentation**: Update this README and add inline documentation

## 📞 Support

For questions about the test suite:

1. Check existing test examples
2. Review the fixtures and utilities
3. Consult the project documentation
4. Create an issue for test-specific questions

