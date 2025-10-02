import json
import os
import re
from typing import Any

from pydantic_settings_sources.errors import MissingEnvVarError

env_var_regex = re.compile(r"\$\{([^:}]+)(?::-([^}]+))?\}")


def _substitute_env_var(match: re.Match) -> str:
    var_name = match.group(1)
    default_value = match.group(2)

    env_value = os.environ.get(var_name)
    if env_value is not None:
        return env_value

    if default_value is not None:
        return default_value

    raise MissingEnvVarError(var_name)


def deep_substitute_env_vars(value: Any) -> Any:
    """
    Recursively substitutes environment variables in a dictionary, list, or string.
    """
    if isinstance(value, dict):
        return {k: deep_substitute_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [deep_substitute_env_vars(v) for v in value]
    if not isinstance(value, str):
        return value

    while env_var_regex.search(value):
        value = env_var_regex.sub(_substitute_env_var, value)

    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value
