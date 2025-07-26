import json
from pathlib import Path
from typing import Dict, List

import pytest
from pydantic import BaseModel
from pydantic_settings import BaseSettings

from pydantic_settings_sources import (
    TomlEnvConfigSettingsSource,
    YamlEnvConfigSettingsSource,
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
        json.dumps(
            [{"key1": "value1", "key2": "value2"}, {"key1": "value3", "key2": "value4"}]
        ),
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
            {
                "level1": {
                    "level2": {"key1": "overridden_value1", "key2": "overridden_value2"}
                }
            }
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
