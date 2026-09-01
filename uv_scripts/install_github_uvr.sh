#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Authors (see git history)
# SPDX-License-Identifier: MIT

# just

set -eo pipefail

# where to install uvr
# ~/.local/bin is a common place for user scripts
UVR_LOCAL_PATH=~/.local/bin
UVR_NAME=uvr
UVR_GIT_NAME=uvr-git
UVR_LOCAL_FULL_NAME=$UVR_LOCAL_PATH/$UVR_NAME

# if exists uvr-git, rename it to uvr
if [[ -L $UVR_LOCAL_PATH/$UVR_GIT_NAME ]]; then

    mv $UVR_LOCAL_PATH/$UVR_GIT_NAME $UVR_LOCAL_PATH/$UVR_NAME # rename uvr-git to uvr
    echo "Renamed $UVR_GIT_NAME to $UVR_NAME"

else

    echo "No existing $UVR_GIT_NAME link found."
    # uv uninstall uvr
    # uv tool install --from git+https://github.com/Oorteo/uvr uvr

fi
