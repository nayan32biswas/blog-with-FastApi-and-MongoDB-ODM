#!/usr/bin/env bash

set -e
set -x

uv run --extra dev mypy app
uv run --extra dev ruff check app scripts
uv run --extra dev ruff format app --check
