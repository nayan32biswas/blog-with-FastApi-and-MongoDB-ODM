#!/usr/bin/env bash

set -e
set -x

uv run ty check app
uv run ruff check app scripts
uv run ruff format app --check
