#!/usr/bin/env bash

CONTAINER=ingestion-swagger

# Kill the previous container
docker kill ${CONTAINER} || true #&& docker rm  ${CONTAINER}

# Starting RabbitMQ with docker
docker run -it --rm -d --hostname localhost -p 8080:8080 --name ${CONTAINER} swaggerapi/swagger-ui
