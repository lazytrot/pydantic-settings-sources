# Testing Guide

This document describes the testing strategy and how to run tests for pydantic-settings-sources.

## Python Version Support

The library supports Python 3.8 through 3.12 with both Pydantic v1 and v2:

| Python Version | Pydantic v1 | Pydantic v2 |
|----------------|-------------|-------------|
| 3.8            | ✅          | ✅          |
| 3.9            | ✅          | ✅          |
| 3.10           | ✅          | ✅          |
| 3.11           | ✅          | ✅          |
| 3.12           | ❌          | ✅          |

**Note:** Python 3.12 does not support Pydantic v1 due to dependency conflicts with PyYAML.

## Test Matrix

### Environments

The test suite is configured to run across the following environments via tox:

- `py38-pydantic1` - Python 3.8 with Pydantic 1.x
- `py38-pydantic2` - Python 3.8 with Pydantic 2.x
- `py39-pydantic1` - Python 3.9 with Pydantic 1.x
- `py39-pydantic2` - Python 3.9 with Pydantic 2.x
- `py310-pydantic1` - Python 3.10 with Pydantic 1.x
- `py310-pydantic2` - Python 3.10 with Pydantic 2.x
- `py311-pydantic1` - Python 3.11 with Pydantic 1.x
- `py311-pydantic2` - Python 3.11 with Pydantic 2.x
- `py312-pydantic2` - Python 3.12 with Pydantic 2.x
- `lint` - Code linting with ruff
- `format` - Code formatting with black

## Running Tests

### Prerequisites

Install development dependencies:

```bash
poetry install
```

### Run All Tests

```bash
poetry run tox
```

### Run Tests for Specific Python Version

```bash
# Python 3.12 with Pydantic 2
poetry run tox -e py312-pydantic2

# Python 3.11 with Pydantic 1
poetry run tox -e py311-pydantic1
```

### Run Only Unit Tests (Current Python Version)

```bash
poetry run pytest
```

### Run Linting

```bash
poetry run tox -e lint
```

### Run Format Check

```bash
poetry run tox -e format
```

### Auto-format Code

```bash
poetry run black .
```

### Fix Linting Issues

```bash
poetry run ruff check . --fix
```

## Test Coverage

The test suite includes 20 comprehensive tests covering:

### Basic Functionality
- ✅ Default values with `${VAR:-default}` syntax
- ✅ Environment variable substitution
- ✅ Missing environment variable errors

### YAML Support
- ✅ Simple YAML configuration
- ✅ Complex nested structures
- ✅ Directory merging (multiple YAML files)
- ✅ Type validation with Pydantic models
- ✅ Case-insensitive field matching
- ✅ Extra fields support

### TOML Support
- ✅ Simple TOML configuration
- ✅ Default values
- ✅ Directory merging (multiple TOML files)

### Integration
- ✅ Mixed sources (YAML + environment variables)
- ✅ Nested Pydantic models
- ✅ Complex data types (lists, dicts, nested objects)
- ✅ Invalid file handling
- ✅ Configuration errors

### API Styles
- ✅ Simplified inheritance-based API (`YamlEnvSettings`, `TomlEnvSettings`)
- ✅ Manual source configuration API
- ✅ ConfigDict integration

## Continuous Integration

The project is configured for GitHub Actions via `gh-actions` in `tox.ini`:

- Python 3.8-3.11: Tests with both Pydantic 1 and 2
- Python 3.12: Tests with Pydantic 2 only, plus linting and formatting

## Troubleshooting

### PyYAML Installation Issues

If you encounter PyYAML installation errors with Python 3.12 and Pydantic 1, this is expected. Use Pydantic 2 with Python 3.12.

### Multiple Python Versions

To test with multiple Python versions locally, use `pyenv`:

```bash
# Install pyenv
curl https://pyenv.run | bash

# Install Python versions
pyenv install 3.8.18
pyenv install 3.9.18
pyenv install 3.10.13
pyenv install 3.11.7
pyenv install 3.12.1

# Make them available
pyenv local 3.8.18 3.9.18 3.10.13 3.11.7 3.12.1

# Run tox (will use all available Python versions)
poetry run tox
```

## Writing New Tests

When adding new tests:

1. Add test functions to `tests/test_sources.py`
2. Follow existing naming conventions: `test_<feature>_<scenario>`
3. Use descriptive docstrings
4. Test both YAML and TOML variants when applicable
5. Ensure tests are independent and can run in any order
6. Run linting and formatting before committing:
   ```bash
   poetry run black .
   poetry run ruff check . --fix
   poetry run pytest
   ```
