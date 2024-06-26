#!/bin/bash
set -eux

runner_os=$1
tag_name=$2

cd dist/

if [ -f "./isic.exe" ]; then
    executable="isic.exe"
else
    executable="isic"
fi

chmod +x $executable
zipfile="isic-cli_${runner_os}.zip"

if [[ "$runner_os" = "Windows" ]]; then
    powershell Compress-Archive $executable $zipfile
else
    zip $zipfile $executable
fi

gh release upload \
    $tag_name \
    "${zipfile}#${runner_os} executable" \
    --clobber
