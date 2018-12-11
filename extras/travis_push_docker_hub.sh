#!/usr/bin/env bash

set -e

## Travis run on master branch and not a PR (this is after a PR has been approved)
if  [ "$TRAVIS_BRANCH" = "master" ] &&
    [ "$TRAVIS_PULL_REQUEST" = "false" ]
then
    make -C images -j 4
    echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USER" --password-stdin
    docker push egarchive/base:latest
    docker push egarchive/inbox:latest
    docker push egarchive/lega:latest
fi
