#!/usr/bin/env bash

set -e
set -x

uv run coverage run -m pytest
uv run coverage combine
uv run coverage report --show-missing
uv run coverage html
