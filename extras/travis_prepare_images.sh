#!/usr/bin/env bash

set -e

# Check if a certain image Dockerfile has changed.
# The current command should be run in the deploy directory.
# If we detect changes against origin/master we build and push a new image.

check_image () {
  if git diff --exit-code origin/master -- "images/$1/Dockerfile" >/dev/null
  then
      echo "New egarchive/$1 docker image is not required."
      docker pull "egarchive/$1"
  else
      echo "egarchive/$1 base image changed, building a new one."
      make -C images "$1"
      echo "pushing new egarchive/$1 image."
      docker push "egarchive/$1"
  fi
}

check_image base
check_image inbox
check_image lega
