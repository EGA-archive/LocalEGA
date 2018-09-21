#!/usr/bin/env bash

# Check if a certain image has changed, in our case either OS or OpenSSH.
# The current command should be run in the docker directory.
# If we detect changes against origin/dev we build and push new image.

check_image(){
  (git diff --exit-code origin/dev -- images/$1/Dockerfile >/dev/null)
  local docker=$?
  if [[ "$docker" == "1" ]]; then
    echo "ega-$1 base image changed, building new ega-$1 image." ;
    make -C images $1 ;
    echo "pushing new ega-$1 image."
    docker push nbisweden/ega-$1 ;
  else
    echo "New ega-$1 docker image is not required." ;
  fi
}

check_image $1
