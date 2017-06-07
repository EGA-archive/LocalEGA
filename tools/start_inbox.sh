#!/usr/bin/env bash

CONTAINER=ega-inbox
# HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# source $HERE/details/db.credentials

# Kill the previous container
docker kill ${CONTAINER} || docker rm ${CONTAINER} || true

# Starting RabbitMQ with docker
docker run -it $* -d --hostname localhost     \
       -p 2222:22 --name ${CONTAINER}         \
       -v /Users/daz/Workspace/NBIS/Local-EGA/code/data/inbox:/home  \
       ega-inbox
# The image includes EXPOSE 22


