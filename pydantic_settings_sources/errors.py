class ConfigSourceError(Exception):
    """Base exception for pydantic-settings-extra-sources."""


class ConfigFileParsingError(ConfigSourceError):
    """Exception raised for errors in parsing a config file."""

    def __init__(self, file_path: str, original_exception: Exception):
        self.file_path = file_path
        self.original_exception = original_exception
        message = f"Error parsing config file at '{file_path}': {original_exception}"
        super().__init__(message)


class MissingEnvVarError(ConfigSourceError):
    """Exception raised for missing environment variables."""

    def __init__(self, var_name: str):
        self.var_name = var_name
        message = f"Missing environment variable '{var_name}' and no default value was provided."
        super().__init__(message)
