#!/usr/bin/env bash

CONTAINER=ega-db
HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $HERE/details/db.credentials

# Kill the previous container
docker kill ${CONTAINER} || docker rm ${CONTAINER} || true

# Starting RabbitMQ with docker
docker run -it $* -d --hostname localhost     \
       -e POSTGRES_PASSWORD=mysecretpassword    \
       -e POSTGRES_USER=postgres                \
       -p 5432:5432 --name ${CONTAINER}         \
       -v $HERE/db.sql:/docker-entrypoint-initdb.d/db.sql \
       postgres
# The image includes EXPOSE 5432

#docker cp $HERE/db.sql ${CONTAINER}:/docker-entrypoint-initdb.d/db.sql

