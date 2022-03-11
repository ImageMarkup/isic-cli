#!/usr/bin/env bash
set -eu

if [[ $# -eq 0 ]] ; then
    echo "version must be supplied e.g. v1.2.3"
    exit 1
fi

readonly VERSION="$1"
shift

git tag "$VERSION" && git push origin "$VERSION" && gh release create "$VERSION" --notes ""
