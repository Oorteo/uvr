#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Authors (see git history)
# SPDX-License-Identifier: MIT

# install local version of uvr in ~/.local/bin

set -eo pipefail

# where to install uvr
# ~/.local/bin is a common place for user scripts
UVR_LOCAL_PATH=~/.local/bin
UVR_NAME=uvr
UVR_GIT_NAME=uvr-git
UVR_LOCAL_FULL_NAME=$UVR_LOCAL_PATH/$UVR_NAME # .local/bin/uvr

# check if script is link use [[  ]]
if [[ -L $UVR_LOCAL_FULL_NAME ]]; then
    LINK_TARGET=$(readlink -f $UVR_LOCAL_FULL_NAME)           # get the target of the link: uvr -> ...
    if [[ $LINK_TARGET == *".local/share"* ]]; then           # this is uvr-git version
        mv $UVR_LOCAL_FULL_NAME $UVR_LOCAL_PATH/$UVR_GIT_NAME # rename uvr to uvr-git
        echo "Renamed $UVR_NAME to $UVR_GIT_NAME"
    else # local version active
        # rm $UVR_LOCAL_FULL_NAME
        # echo "Removed existing link at $UVR_LOCAL_FULL_NAME"
        echo "local version active: $LINK_TARGET"
        exit 0
    fi
fi

# git root directory
GIT_ROOT_DIR=$(git rev-parse --show-toplevel)

# if not installed create symbolic link to local uvr.py, and use force to overwrite existing link
ln -s -f $GIT_ROOT_DIR/src/uvr/uvr.py $UVR_LOCAL_FULL_NAME

echo "Installed $UVR_NAME to $UVR_LOCAL_FULL_NAME"
echo "Make sure $UVR_LOCAL_PATH is in your PATH"
