#!/usr/bin/env bash


check_image(){
  (git diff --exit-status origin/dev docker/images/os/Dockerfile >/dev/null)
  local docker=$?
  if [[ "$docker" == "0" || "$docker" == "128" ]]; then
    echo "$1 base image changed, building new $1 image." ;
    make -C images $1 ;
    docker push nbisweden/ega-$1 ;
  else
    echo "New $1 docker image is not required." ;
  fi
}

check_image os
check_image openssh
