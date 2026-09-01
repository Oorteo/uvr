#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Authors (see git history)
# SPDX-License-Identifier: MIT

set -e

# uvr pytest
#uvr pytest --cov-report term-missing --cov-report html --cov-report xml --cov=uvr

GIT_ROOT_DIR=$(git rev-parse --show-toplevel)
cd $GIT_ROOT_DIR
echo "Current working directory: $(pwd)"

# uvr full path, maybe use type uvr to find it
UVR=$(type -p uvr)
echo "Using uvr at: $UVR"
if [[ -L $UVR ]]; then
    UVR=$(readlink -f $UVR) # resolve symlink to the actual file
    echo "Resolved uvr to: $UVR"
fi

uvr pytest --cov=uvr --cov-report html:coverage --cov-report xml --cov-report term
