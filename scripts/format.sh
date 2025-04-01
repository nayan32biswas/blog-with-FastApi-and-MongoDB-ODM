#!/usr/bin/env bash

set -x

ruff check app scripts --fix
ruff format app scripts
