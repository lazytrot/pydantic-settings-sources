import os
from typing import Any, Dict

import toml
import yaml
from pydantic_settings.sources import (
    PydanticBaseSettingsSource,
)
from pydantic_settings_sources.errors import ConfigFileParsingError, MissingEnvVarError
from pydantic_settings_sources.utils import deep_substitute_env_vars
from deepmerge import always_merger

__all__ = ["TomlEnvConfigSettingsSource", "YamlEnvConfigSettingsSource"]


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
            with open(file_path, "r", encoding=self.toml_file_encoding) as f:
                return toml.load(f) or {}
        except Exception as e:
            raise ConfigFileParsingError(file_path, e)

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
            with open(file_path, "r", encoding=self.yaml_file_encoding) as f:
                return yaml.safe_load(f) or {}
        except MissingEnvVarError as e:
            raise e
        except Exception as e:
            raise ConfigFileParsingError(file_path, e)

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
