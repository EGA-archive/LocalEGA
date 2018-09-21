#!/usr/bin/env bash

DOCKER_IMAGES=(nbisweden/ega-base nbisweden/ega-inbox)

retag_image() {
    base=$1
    from=$2
    to=$3
    push=$4
    docker pull "${base}:${from}"
    docker tag "${base}:${from}" "${base}:${to}"
    if ${push}; then
      echo "Pushing LocalEGA image: ${base}:${to}"
      docker push "${base}:${to}"
    fi
}

retag_images() {
    from=$1
    to=$2
    push=$3
    for img in "${DOCKER_IMAGES[@]}"; do
        retag_image $img "$from" "$to" $push
    done
}

echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USER" --password-stdin ;

## Travis run on dev branch and not a PR (this is after a PR has been approved)
if [[ "$TRAVIS_BRANCH" == "dev" && "$TRAVIS_PULL_REQUEST" == "false" ]]; then
    retag_images "PR${TRAVIS_PULL_REQUEST}" "latest" true
fi

# When we push a tag we will retag latest with that tag
if [[ "$TRAVIS_TAG" != "" && "$TRAVIS_PULL_REQUEST" == "false" ]]; then
    retag_images "latest" "${TRAVIS_TAG}" true
fi

if [[ "$TRAVIS_PULL_REQUEST" != "false" && "$TRAVIS_PULL_REQUEST" != "" && "$TRAVIS_BUILD_STAGE_NAME" == "Integration tests" ]]; then
    retag_images "PR${TRAVIS_PULL_REQUEST}" "dev" false
fi
