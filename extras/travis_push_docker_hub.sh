#!/usr/bin/env bash

DOCKER_IMAGES=(nbissweden/ega-base nbissweden/ega-inbox)

retag_image() {
    base=$1
    from=$2
    to=$3
    docker pull "${base}:${from}"
    docker tag "${base}:${from}" "${base}:${to}"
    docker push "${base}:${to}"
}

retag_images() {
    from=$1
    to=$2
    for img in "${DOCKER_IMAGES[@]}"; do
        retag_image $img "$from" "$to"
    done
}

echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USER" --password-stdin ;

## Travis run on dev branch and not a PR (this is after a PR has been approved)
if [[ "$TRAVIS_BRANCH" == "dev" && "$TRAVIS_PULL_REQUEST" == "false" ]]; then
    retag_images "latest" "dev"
fi

if [[ "$TRAVIS_TAG" != "" ]]; then
    ## TODO should we just retag :dev in this case?? What happens if we have multiple builds at the same time?
    retag_images "dev" "$TRAVIS_TAG"
fi

if [[ "$TRAVIS_PULL_REQUEST" != "false" && "$TRAVIS_PULL_REQUEST" != "" ]]; then
    retag_images "dev" "PR${TRAVIS_PULL_REQUEST}"
fi
