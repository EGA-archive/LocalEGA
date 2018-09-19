#!/usr/bin/env bash


check_image(){
  (git diff --name-only ${TRAVIS_COMMIT_RANGE} | grep docker/images/$1/Dockerfile >/dev/null)
  local docker=$?
  if [[ "$osdocker" == "0" ]]; then
    echo "$1 base image changed, building new $1 image." ;
    make -C images $1 ;
    docker push nbisweden/ega-$1 ;
  else
    echo "New $1 docker image is not required." ;
  fi
}

check_image os
check_image openssh
