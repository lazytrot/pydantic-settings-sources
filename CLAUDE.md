# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Setup and Dependencies

This project uses Poetry for dependency management. To install dependencies, run:

```bash
poetry install
```

## Commands

- **Run tests and linting:** `poetry run tox`
- **Run tests for a specific python version:** `poetry run tox -e py311`
- **Linting:** `poetry run tox -e lint`
- **Formatting:** `poetry run tox -e format`
- **Auto-formatting:** `poetry run black .`


## Architecture

The project aims to provide extra sources for `pydantic-settings`, such as YAML and TOML files, allowing for environment variable overrides. The main logic will be in the `pydantic_settings_extra_sources` directory.
