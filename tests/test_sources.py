import json
from pathlib import Path
from typing import Dict, List

import pytest
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from pydantic_settings_sources import (
    TomlEnvConfigSettingsSource,
    TomlEnvSettings,
    YamlEnvConfigSettingsSource,
    YamlEnvSettings,
)
from pydantic_settings_sources.errors import ConfigFileParsingError, MissingEnvVarError


class SubConfigModel(BaseModel):
    key1: str
    key2: str


class ConfigModel(BaseSettings):
    string_value: str
    integer_value: int
    float_value: float
    boolean_value: bool
    list_value: List[str]
    dict_value: Dict[str, str]
    list_of_dicts_value: List[SubConfigModel]
    nested_dict_value: Dict[str, Dict[str, Dict[str, str]]]


@pytest.fixture
def config_path(request, tmp_path):
    config_file = request.param
    config_content = Path(f"tests/data/{config_file}").read_text()
    config_path = tmp_path / config_file
    config_path.write_text(config_content)
    return config_path


@pytest.fixture
def source_kwargs(request, config_path):
    if request.param == YamlEnvConfigSettingsSource:
        return {"yaml_file": config_path, "yaml_file_encoding": "utf-8"}
    elif request.param == TomlEnvConfigSettingsSource:
        return {"toml_file": config_path, "toml_file_encoding": "utf-8"}
    return {}


@pytest.mark.parametrize(
    "config_path, source_class, source_kwargs",
    [
        ("config.yaml", YamlEnvConfigSettingsSource, YamlEnvConfigSettingsSource),
        ("config.toml", TomlEnvConfigSettingsSource, TomlEnvConfigSettingsSource),
    ],
    indirect=["config_path", "source_kwargs"],
)
def test_source_default_values(config_path, source_class, source_kwargs, monkeypatch):
    monkeypatch.setenv("STRING_VALUE", "default_string")
    monkeypatch.setenv("INTEGER_VALUE", "123")
    monkeypatch.setenv("FLOAT_VALUE", "123.45")
    monkeypatch.setenv("BOOLEAN_VALUE", "true")
    monkeypatch.setenv("LIST_VALUE", json.dumps(["a", "b", "c"]))
    monkeypatch.setenv("DICT_VALUE", json.dumps({"key1": "value1", "key2": "value2"}))
    monkeypatch.setenv(
        "LIST_OF_DICTS_VALUE",
        json.dumps([{"key1": "value1", "key2": "value2"}, {"key1": "value3", "key2": "value4"}]),
    )
    monkeypatch.setenv(
        "NESTED_DICT_VALUE",
        json.dumps({"level1": {"level2": {"key1": "value1", "key2": "value2"}}}),
    )

    class Settings(ConfigModel):
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
                source_class(cls, **source_kwargs),
                env_settings,
                dotenv_settings,
                file_secret_settings,
            )

    settings = Settings()
    assert settings.string_value == "default_string"
    assert settings.integer_value == 123
    assert settings.float_value == 123.45
    assert isinstance(settings.float_value, float)
    assert settings.boolean_value is True
    assert settings.list_value == ["a", "b", "c"]
    assert settings.dict_value == {"key1": "value1", "key2": "value2"}
    assert settings.list_of_dicts_value == [
        SubConfigModel(key1="value1", key2="value2"),
        SubConfigModel(key1="value3", key2="value4"),
    ]
    assert settings.nested_dict_value == {
        "level1": {"level2": {"key1": "value1", "key2": "value2"}}
    }


@pytest.mark.parametrize(
    "config_path, source_class, source_kwargs",
    [
        ("config.yaml", YamlEnvConfigSettingsSource, YamlEnvConfigSettingsSource),
        ("config.toml", TomlEnvConfigSettingsSource, TomlEnvConfigSettingsSource),
    ],
    indirect=["config_path", "source_kwargs"],
)
def test_source_env_var_override(config_path, source_class, source_kwargs, monkeypatch):
    monkeypatch.setenv("STRING_VALUE", "overridden_string")
    monkeypatch.setenv("INTEGER_VALUE", "456")
    monkeypatch.setenv("FLOAT_VALUE", "456.78")
    monkeypatch.setenv("BOOLEAN_VALUE", "false")
    monkeypatch.setenv("LIST_VALUE", json.dumps(["x", "y", "z"]))
    monkeypatch.setenv(
        "DICT_VALUE",
        json.dumps({"key1": "overridden_value1", "key2": "overridden_value2"}),
    )
    monkeypatch.setenv(
        "LIST_OF_DICTS_VALUE",
        json.dumps(
            [
                {"key1": "overridden_value1", "key2": "overridden_value2"},
                {"key1": "overridden_value3", "key2": "overridden_value4"},
            ]
        ),
    )
    monkeypatch.setenv(
        "NESTED_DICT_VALUE",
        json.dumps(
            {"level1": {"level2": {"key1": "overridden_value1", "key2": "overridden_value2"}}}
        ),
    )

    class Settings(ConfigModel):
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
                source_class(cls, **source_kwargs),
                env_settings,
                dotenv_settings,
                file_secret_settings,
            )

    settings = Settings()
    assert settings.string_value == "overridden_string"
    assert settings.integer_value == 456
    assert settings.float_value == 456.78
    assert isinstance(settings.float_value, float)
    assert settings.boolean_value is False
    assert settings.list_value == ["x", "y", "z"]
    assert settings.dict_value == {
        "key1": "overridden_value1",
        "key2": "overridden_value2",
    }
    assert settings.list_of_dicts_value == [
        SubConfigModel(key1="overridden_value1", key2="overridden_value2"),
        SubConfigModel(key1="overridden_value3", key2="overridden_value4"),
    ]
    assert settings.nested_dict_value == {
        "level1": {
            "level2": {
                "key1": "overridden_value1",
                "key2": "overridden_value2",
            }
        }
    }


def test_source_invalid_file(tmp_path):
    config_content = "string_value: -"
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_content)
    with pytest.raises(ConfigFileParsingError):

        class Settings(ConfigModel):
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
                        cls, yaml_file=config_path, yaml_file_encoding="utf-8"
                    ),
                    env_settings,
                    dotenv_settings,
                    file_secret_settings,
                )

        Settings()


def test_missing_env_var(tmp_path):
    config_content = "string_value: ${MISSING_VAR}"
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_content)
    with pytest.raises(MissingEnvVarError):

        class Settings(ConfigModel):
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
                        cls, yaml_file=config_path, yaml_file_encoding="utf-8"
                    ),
                    env_settings,
                    dotenv_settings,
                    file_secret_settings,
                )

        Settings()


# Tests for simplified API using inheritance
def test_yaml_env_settings_simple(tmp_path, monkeypatch):
    config_content = """
string_value: ${STRING_VALUE}
integer_value: ${INTEGER_VALUE}
"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_content)

    monkeypatch.setenv("STRING_VALUE", "test_string")
    monkeypatch.setenv("INTEGER_VALUE", "42")

    class Settings(YamlEnvSettings):
        model_config = SettingsConfigDict(
            yaml_file=str(config_path),
            extra="allow",
            case_sensitive=False,
        )

        string_value: str
        integer_value: int

    settings = Settings()
    assert settings.string_value == "test_string"
    assert settings.integer_value == 42


def test_toml_env_settings_simple(tmp_path, monkeypatch):
    config_content = """
string_value = "${STRING_VALUE}"
integer_value = "${INTEGER_VALUE}"
"""
    config_path = tmp_path / "config.toml"
    config_path.write_text(config_content)

    monkeypatch.setenv("STRING_VALUE", "test_string")
    monkeypatch.setenv("INTEGER_VALUE", "42")

    class Settings(TomlEnvSettings):
        model_config = SettingsConfigDict(
            toml_file=str(config_path),
            extra="allow",
            case_sensitive=False,
        )

        string_value: str
        integer_value: int

    settings = Settings()
    assert settings.string_value == "test_string"
    assert settings.integer_value == 42


def test_yaml_env_settings_missing_file_config():
    with pytest.raises(ValueError, match="yaml_file must be specified"):

        class Settings(YamlEnvSettings):
            model_config = SettingsConfigDict()

            string_value: str

        Settings()


def test_toml_env_settings_missing_file_config():
    with pytest.raises(ValueError, match="toml_file must be specified"):

        class Settings(TomlEnvSettings):
            model_config = SettingsConfigDict()

            string_value: str

        Settings()


# Comprehensive end-to-end tests
def test_yaml_env_settings_with_defaults(tmp_path, monkeypatch):
    """Test YAML with default values using ${VAR:-default} syntax"""
    config_content = """
database:
  host: ${DB_HOST:-localhost}
  port: ${DB_PORT:-5432}
  name: ${DB_NAME}
api_key: ${API_KEY:-default_key}
debug: ${DEBUG:-false}
"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_content)

    monkeypatch.setenv("DB_NAME", "production_db")

    class Settings(YamlEnvSettings):
        model_config = SettingsConfigDict(
            yaml_file=str(config_path),
            extra="allow",
        )

    settings = Settings()
    assert settings.database["host"] == "localhost"  # default used
    assert settings.database["port"] == 5432  # default used (YAML parses as int)
    assert settings.database["name"] == "production_db"  # env var used
    assert settings.api_key == "default_key"  # default used
    assert not settings.debug  # default used (YAML parses as bool)


def test_yaml_env_settings_complex_nested_structures(tmp_path, monkeypatch):
    """Test complex nested structures with env vars"""
    config_content = """
app:
  name: ${APP_NAME}
  version: ${APP_VERSION:-1.0.0}
  database:
    primary:
      host: ${PRIMARY_DB_HOST}
      port: ${PRIMARY_DB_PORT:-5432}
      credentials:
        username: ${PRIMARY_DB_USER}
        password: ${PRIMARY_DB_PASS}
    replicas: ${DB_REPLICAS}
  features:
    enabled: ${FEATURES_ENABLED}
"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_content)

    monkeypatch.setenv("APP_NAME", "myapp")
    monkeypatch.setenv("PRIMARY_DB_HOST", "db.example.com")
    monkeypatch.setenv("PRIMARY_DB_USER", "admin")
    monkeypatch.setenv("PRIMARY_DB_PASS", "secret123")
    monkeypatch.setenv("DB_REPLICAS", json.dumps(["replica1.example.com", "replica2.example.com"]))
    monkeypatch.setenv("FEATURES_ENABLED", json.dumps(["feature_a", "feature_b"]))

    class Settings(YamlEnvSettings):
        model_config = SettingsConfigDict(
            yaml_file=str(config_path),
            extra="allow",
        )

    settings = Settings()
    assert settings.app["name"] == "myapp"
    assert settings.app["version"] == "1.0.0"  # default
    assert settings.app["database"]["primary"]["host"] == "db.example.com"
    assert settings.app["database"]["primary"]["port"] == 5432  # default (YAML parses as int)
    assert settings.app["database"]["primary"]["credentials"]["username"] == "admin"
    assert settings.app["database"]["primary"]["credentials"]["password"] == "secret123"
    assert settings.app["database"]["replicas"] == [
        "replica1.example.com",
        "replica2.example.com",
    ]
    assert settings.app["features"]["enabled"] == ["feature_a", "feature_b"]


def test_yaml_env_settings_directory_merge(tmp_path, monkeypatch):
    """Test loading and merging multiple YAML files from a directory"""
    config_dir = tmp_path / "yaml_config"
    config_dir.mkdir()

    # Base config
    (config_dir / "01_base.yaml").write_text(
        """
app:
  name: ${APP_NAME}
  timeout: ${TIMEOUT:-30}
database:
  host: ${DB_HOST:-localhost}
"""
    )

    # Override config
    (config_dir / "02_override.yaml").write_text(
        """
app:
  debug: ${DEBUG:-false}
database:
  port: ${DB_PORT:-5432}
  ssl: ${DB_SSL:-true}
"""
    )

    monkeypatch.setenv("APP_NAME", "testapp_yaml")

    class Settings(YamlEnvSettings):
        model_config = SettingsConfigDict(
            yaml_file=str(config_dir),
            extra="allow",
        )

    settings = Settings()
    # Check merged values
    assert settings.app["name"] == "testapp_yaml"
    assert settings.app["timeout"] == 30  # YAML parses as int
    assert not settings.app["debug"]  # YAML parses as bool
    assert settings.database["host"] == "localhost"
    assert settings.database["port"] == 5432  # YAML parses as int
    assert settings.database["ssl"]  # YAML parses as bool


def test_toml_env_settings_with_defaults(tmp_path, monkeypatch):
    """Test TOML with default values using ${VAR:-default} syntax"""
    config_content = """
api_key = "${API_KEY:-default_key}"
debug = "${DEBUG:-false}"

[database]
host = "${DB_HOST:-localhost}"
port = "${DB_PORT:-5432}"
name = "${DB_NAME}"
"""
    config_path = tmp_path / "config.toml"
    config_path.write_text(config_content)

    monkeypatch.setenv("DB_NAME", "production_db")

    class Settings(TomlEnvSettings):
        model_config = SettingsConfigDict(
            toml_file=str(config_path),
            extra="allow",
        )

    settings = Settings()
    assert settings.database["host"] == "localhost"  # default used
    assert settings.database["port"] == 5432  # default used (parsed from string)
    assert settings.database["name"] == "production_db"  # env var used
    assert settings.api_key == "default_key"  # default used
    assert not settings.debug  # default used (parsed from string)


def test_yaml_env_settings_with_typed_fields(tmp_path, monkeypatch):
    """Test that pydantic validates types correctly with env var substitution"""
    config_content = """
name: ${APP_NAME}
port: ${APP_PORT}
timeout: ${APP_TIMEOUT}
enabled: ${APP_ENABLED}
tags: ${APP_TAGS}
"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_content)

    monkeypatch.setenv("APP_NAME", "myapp")
    monkeypatch.setenv("APP_PORT", "8080")
    monkeypatch.setenv("APP_TIMEOUT", "30.5")
    monkeypatch.setenv("APP_ENABLED", "true")
    monkeypatch.setenv("APP_TAGS", json.dumps(["web", "api", "v1"]))

    class Settings(YamlEnvSettings):
        model_config = SettingsConfigDict(
            yaml_file=str(config_path),
        )

        name: str
        port: int
        timeout: float
        enabled: bool
        tags: List[str]

    settings = Settings()
    assert settings.name == "myapp"
    assert settings.port == 8080
    assert isinstance(settings.port, int)
    assert settings.timeout == 30.5
    assert isinstance(settings.timeout, float)
    assert settings.enabled is True
    assert isinstance(settings.enabled, bool)
    assert settings.tags == ["web", "api", "v1"]


def test_yaml_env_settings_case_insensitive(tmp_path, monkeypatch):
    """Test case-insensitive field matching with extra='allow'"""
    config_content = """
database_url: ${DB_URL}
api_key: ${API_KEY}
debug_mode: ${DEBUG}
"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_content)

    monkeypatch.setenv("DB_URL", "postgresql://localhost/db")
    monkeypatch.setenv("API_KEY", "secret")
    monkeypatch.setenv("DEBUG", "true")

    class Settings(YamlEnvSettings):
        model_config = SettingsConfigDict(
            yaml_file=str(config_path),
            case_sensitive=False,
            extra="allow",
        )

        database_url: str
        api_key: str
        debug_mode: bool

    settings = Settings()
    assert settings.database_url == "postgresql://localhost/db"
    assert settings.api_key == "secret"
    assert settings.debug_mode is True  # YAML parses "true" as bool


def test_yaml_env_settings_extra_allow(tmp_path, monkeypatch):
    """Test that extra='allow' permits additional fields from YAML"""
    config_content = """
name: ${APP_NAME}
port: ${APP_PORT}
extra_field_1: ${EXTRA_1}
extra_field_2: ${EXTRA_2:-default_extra}
"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_content)

    monkeypatch.setenv("APP_NAME", "testapp")
    monkeypatch.setenv("APP_PORT", "9000")
    monkeypatch.setenv("EXTRA_1", "extra_value")

    class Settings(YamlEnvSettings):
        model_config = SettingsConfigDict(
            yaml_file=str(config_path),
            extra="allow",
        )

        name: str
        port: int

    settings = Settings()
    assert settings.name == "testapp"
    assert settings.port == 9000
    assert settings.extra_field_1 == "extra_value"
    assert settings.extra_field_2 == "default_extra"


def test_yaml_env_settings_mixed_sources(tmp_path, monkeypatch):
    """Test that settings can come from both YAML and environment variables"""
    config_content = """
from_yaml: ${YAML_VAR}
"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_content)

    monkeypatch.setenv("YAML_VAR", "yaml_value")
    monkeypatch.setenv("FROM_ENV", "env_value")

    class Settings(YamlEnvSettings):
        model_config = SettingsConfigDict(
            yaml_file=str(config_path),
        )

        from_yaml: str
        from_env: str = "default"

    settings = Settings()
    assert settings.from_yaml == "yaml_value"
    # Environment variable should override default
    assert settings.from_env == "env_value"


def test_toml_directory_merge(tmp_path, monkeypatch):
    """Test loading and merging multiple TOML files from a directory"""
    config_dir = tmp_path / "toml_config"
    config_dir.mkdir()

    # Base config
    (config_dir / "01_base.toml").write_text(
        """
[app]
name = "${APP_NAME}"
timeout = "${TIMEOUT:-30}"

[database]
host = "${DB_HOST:-localhost}"
"""
    )

    # Override config
    (config_dir / "02_override.toml").write_text(
        """
[app]
debug = "${DEBUG:-false}"

[database]
port = "${DB_PORT:-5432}"
ssl = "${DB_SSL:-true}"
"""
    )

    monkeypatch.setenv("APP_NAME", "testapp_toml")

    class Settings(TomlEnvSettings):
        model_config = SettingsConfigDict(
            toml_file=str(config_dir),
            extra="allow",
        )

    settings = Settings()
    # Check merged values
    assert settings.app["name"] == "testapp_toml"
    assert settings.app["timeout"] == 30  # Parsed from string
    assert not settings.app["debug"]  # Parsed from string
    assert settings.database["host"] == "localhost"
    assert settings.database["port"] == 5432  # Parsed from string
    assert settings.database["ssl"]  # Parsed from string


def test_yaml_env_settings_with_pydantic_models(tmp_path, monkeypatch):
    """Test using nested Pydantic models with YAML config"""
    config_content = """
database:
  host: ${DB_HOST}
  port: ${DB_PORT}
  credentials:
    username: ${DB_USER}
    password: ${DB_PASS}
"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_content)

    monkeypatch.setenv("DB_HOST", "db.example.com")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_USER", "admin")
    monkeypatch.setenv("DB_PASS", "secret")

    class Credentials(BaseModel):
        username: str
        password: str

    class Database(BaseModel):
        host: str
        port: int
        credentials: Credentials

    class Settings(YamlEnvSettings):
        model_config = SettingsConfigDict(
            yaml_file=str(config_path),
        )

        database: Database

    settings = Settings()
    assert settings.database.host == "db.example.com"
    assert settings.database.port == 5432
    assert settings.database.credentials.username == "admin"
    assert settings.database.credentials.password == "secret"
