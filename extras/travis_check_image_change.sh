#!/usr/bin/env bash

# Check if a certain image has changed, in our case either OS or OpenSSH.
# The current command should be run in the docker directory.
# If we detect changes against origin/dev we build and push new image.

check_image () {
  if git diff --exit-code origin/dev -- "images/$1/Dockerfile"
  then
    printf 'New ega-%s docker image is not required.\n' "$1"
  else
    printf 'ega-%s base image changed, building new ega-%s image.\n' "$1" "$1"
    make -C images "$1"
    printf 'pushing new ega-%s image.\n' "$1"
    docker push "nbisweden/ega-$1"
  fi
}

check_image "$1"
