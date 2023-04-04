#!/usr/bin/env bash

set -e
set -x

mypy app --no-namespace-packages
flake8 app
black app --check
isort app scripts --check-only
