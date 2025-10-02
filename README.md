# pydantic-settings-extra-sources

Extra configuration sources for [pydantic-settings](https://github.com/pydantic/pydantic-settings) that enable loading settings from YAML and TOML files with environment variable substitution.

## Features

- **YAML and TOML Support**: Load configuration from YAML and TOML files
- **Environment Variable Substitution**: Reference environment variables directly in config files using `${ENV_VAR}` syntax
- **Default Values**: Provide fallback values with `${ENV_VAR:-default_value}` syntax
- **Complex Type Support**: Handles strings, integers, floats, booleans, lists, dictionaries, and nested structures
- **Directory Merging**: Load and merge multiple config files from a directory
- **Type-Safe**: Full integration with Pydantic's validation and type checking

## Installation

```bash
poetry add pydantic-settings-extra-sources
```

## Quick Start

### 1. Create a YAML config file

```yaml
# config.yaml
database:
  host: ${DB_HOST:-localhost}
  port: ${DB_PORT:-5432}
  name: ${DB_NAME}
api_key: ${API_KEY}
debug: ${DEBUG:-false}
```

### 2. Define your settings model

```python
from pydantic import Field
from pydantic_settings import SettingsConfigDict
from pydantic_settings_sources import YamlEnvSettings

class Settings(YamlEnvSettings):
    model_config = SettingsConfigDict(
        yaml_file="config.yaml",
        extra="allow",
        case_sensitive=False,
    )

    database: dict
    api_key: str
    debug: bool = False

# Load settings - environment variables will be substituted
settings = Settings()
```

### 3. Set environment variables and run

```bash
export DB_NAME=myapp
export API_KEY=secret123
python app.py
```

## Usage

### Simple Inheritance (Recommended)

**YAML:**
```python
from pydantic_settings import SettingsConfigDict
from pydantic_settings_sources import YamlEnvSettings

class Settings(YamlEnvSettings):
    model_config = SettingsConfigDict(
        yaml_file="config.yaml",  # Path to YAML file or directory
        yaml_file_encoding="utf-8",  # Optional, defaults to utf-8
        extra="allow",  # Optional: allow extra fields from YAML
        case_sensitive=False,  # Optional: case-insensitive field matching
    )

    # Your fields here
    database_url: str
    debug: bool = False
```

**TOML:**
```python
from pydantic_settings import SettingsConfigDict
from pydantic_settings_sources import TomlEnvSettings

class Settings(TomlEnvSettings):
    model_config = SettingsConfigDict(
        toml_file="config.toml",  # Path to TOML file or directory
        toml_file_encoding="utf-8",  # Optional, defaults to utf-8
        extra="allow",  # Optional: allow extra fields from TOML
        case_sensitive=False,  # Optional: case-insensitive field matching
    )

    # Your fields here
    database_url: str
    debug: bool = False
```

### Advanced: Manual Source Configuration

If you need more control over the settings sources order:

```python
from pydantic_settings import BaseSettings
from pydantic_settings_sources import YamlEnvConfigSettingsSource

class Settings(BaseSettings):
    database_url: str
    debug: bool = False

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (
            init_settings,
            YamlEnvConfigSettingsSource(
                cls,
                yaml_file="config.yaml",
                yaml_file_encoding="utf-8"
            ),
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )
```

### Environment Variable Syntax

**Required variable:**
```yaml
api_key: ${API_KEY}  # Throws MissingEnvVarError if API_KEY not set
```

**With default value:**
```yaml
host: ${HOST:-localhost}  # Uses "localhost" if HOST not set
port: ${PORT:-8080}       # Uses "8080" if PORT not set
```

### Complex Types

Environment variables containing JSON are automatically parsed:

```bash
# Set complex environment variables
export LIST_VALUE='["item1", "item2", "item3"]'
export DICT_VALUE='{"key1": "value1", "key2": "value2"}'
export NESTED_VALUE='{"level1": {"level2": {"key": "value"}}}'
```

```yaml
# config.yaml
items: ${LIST_VALUE}
mapping: ${DICT_VALUE}
nested: ${NESTED_VALUE}
```

### Loading from Directories

When pointing to a directory, all `.yaml`/`.yml` or `.toml` files are loaded and deep-merged:

```python
YamlEnvConfigSettingsSource(
    settings_cls,
    yaml_file="./config",  # Directory path
    yaml_file_encoding="utf-8"
)
```

Files are processed in alphabetical order, with later files overriding earlier ones.

## Error Handling

```python
from pydantic_settings_extra_sources.errors import MissingEnvVarError, ConfigFileParsingError

try:
    settings = Settings()
except MissingEnvVarError as e:
    print(f"Missing required environment variable: {e}")
except ConfigFileParsingError as e:
    print(f"Failed to parse config file: {e}")
```

## How It Works

The library reads environment variables **directly from your YAML/TOML configuration files** by:

1. Loading the config file(s)
2. Finding all `${ENV_VAR}` or `${ENV_VAR:-default}` patterns
3. Substituting them with values from `os.environ`
4. Parsing JSON values for complex types
5. Returning the resolved configuration to pydantic-settings

This approach keeps your configuration structure in files while allowing environment-specific values to be injected at runtime.

## Development

See [CLAUDE.md](CLAUDE.md) for development setup and commands.

## License

See [LICENCE](LICENCE) file.
