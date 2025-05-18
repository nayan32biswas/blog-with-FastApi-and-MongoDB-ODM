#!/usr/bin/env bash

set -x

uv run --extra dev ruff check app scripts --fix
uv run --extra dev ruff format app scripts
