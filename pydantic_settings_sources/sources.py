import os
from typing import Any, Dict, Tuple

import toml
import yaml
from deepmerge import always_merger
from pydantic_settings import BaseSettings
from pydantic_settings.sources import (
    PydanticBaseSettingsSource,
)

from pydantic_settings_sources.errors import ConfigFileParsingError, MissingEnvVarError
from pydantic_settings_sources.utils import deep_substitute_env_vars

__all__ = [
    "TomlEnvConfigSettingsSource",
    "YamlEnvConfigSettingsSource",
    "YamlEnvSettings",
    "TomlEnvSettings",
]


class TomlEnvConfigSettingsSource(PydanticBaseSettingsSource):
    """
    A settings source that reads from a TOML file and supports environment variable overrides.
    """

    def __init__(self, settings_cls, toml_file, toml_file_encoding):
        super().__init__(settings_cls)
        self.toml_file = toml_file
        self.toml_file_encoding = toml_file_encoding

    def _load_toml_file(self, file_path):
        try:
            with open(file_path, encoding=self.toml_file_encoding) as f:
                return toml.load(f) or {}
        except Exception as e:
            raise ConfigFileParsingError(file_path, e) from e

    def get_field_value(self, field, field_name):
        return None, None, False

    def __call__(self) -> Dict[str, Any]:
        config = {}
        try:
            if os.path.isdir(self.toml_file):
                for root, _, files in os.walk(self.toml_file):
                    for file in sorted(files):
                        if file.endswith(".toml"):
                            file_path = os.path.join(root, file)
                            always_merger.merge(config, self._load_toml_file(file_path))
            elif os.path.isfile(self.toml_file):
                config = self._load_toml_file(self.toml_file)

            return deep_substitute_env_vars(config)
        except MissingEnvVarError as e:
            raise ConfigFileParsingError(self.toml_file, e) from e


class YamlEnvConfigSettingsSource(PydanticBaseSettingsSource):
    """
    A settings source that reads from a YAML file and supports environment variable overrides.
    """

    def __init__(self, settings_cls, yaml_file, yaml_file_encoding):
        super().__init__(settings_cls)
        self.yaml_file = yaml_file
        self.yaml_file_encoding = yaml_file_encoding

    def _load_yaml_file(self, file_path):
        try:
            with open(file_path, encoding=self.yaml_file_encoding) as f:
                return yaml.safe_load(f) or {}
        except MissingEnvVarError as e:
            raise e
        except Exception as e:
            raise ConfigFileParsingError(file_path, e) from e

    def get_field_value(self, field, field_name):
        return None, None, False

    def __call__(self) -> Dict[str, Any]:
        config = {}
        try:
            if os.path.isdir(self.yaml_file):
                for root, _, files in os.walk(self.yaml_file):
                    for file in sorted(files):
                        if file.endswith((".yaml", ".yml")):
                            file_path = os.path.join(root, file)
                            always_merger.merge(config, self._load_yaml_file(file_path))
            elif os.path.isfile(self.yaml_file):
                config = self._load_yaml_file(self.yaml_file)

            return deep_substitute_env_vars(config)
        except MissingEnvVarError as e:
            raise e
        except ConfigFileParsingError as e:
            raise e


class YamlEnvSettings(BaseSettings):
    """
    Base settings class that automatically loads from YAML files with environment variable substitution.

    Configure using model_config:
        - yaml_file: Path to YAML file or directory (required)
        - yaml_file_encoding: File encoding (default: "utf-8")
        - extra: "allow" to accept extra fields from YAML
        - case_sensitive: False for case-insensitive field matching

    Example:
        class Settings(YamlEnvSettings):
            model_config = SettingsConfigDict(
                yaml_file="config.yaml",
                yaml_file_encoding="utf-8",
                extra="allow",
                case_sensitive=False,
            )

            database_url: str
            debug: bool = False
    """

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        config = cls.model_config
        yaml_file = config.get("yaml_file")
        if yaml_file is None:
            raise ValueError("yaml_file must be specified in model_config")

        yaml_file_encoding = config.get("yaml_file_encoding", "utf-8")

        return (
            init_settings,
            YamlEnvConfigSettingsSource(
                settings_cls,
                yaml_file=yaml_file,
                yaml_file_encoding=yaml_file_encoding,
            ),
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


class TomlEnvSettings(BaseSettings):
    """
    Base settings class that automatically loads from TOML files with environment variable substitution.

    Configure using model_config:
        - toml_file: Path to TOML file or directory (required)
        - toml_file_encoding: File encoding (default: "utf-8")
        - extra: "allow" to accept extra fields from TOML
        - case_sensitive: False for case-insensitive field matching

    Example:
        class Settings(TomlEnvSettings):
            model_config = SettingsConfigDict(
                toml_file="config.toml",
                toml_file_encoding="utf-8",
                extra="allow",
                case_sensitive=False,
            )

            database_url: str
            debug: bool = False
    """

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        config = cls.model_config
        toml_file = config.get("toml_file")
        if toml_file is None:
            raise ValueError("toml_file must be specified in model_config")

        toml_file_encoding = config.get("toml_file_encoding", "utf-8")

        return (
            init_settings,
            TomlEnvConfigSettingsSource(
                settings_cls,
                toml_file=toml_file,
                toml_file_encoding=toml_file_encoding,
            ),
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )
