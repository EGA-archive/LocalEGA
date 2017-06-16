#!/usr/bin/env bash

CONTAINER=ega-inbox
HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $HERE/details/inbox

# Kill the previous container
docker kill ${CONTAINER} || docker rm ${CONTAINER} || true

# Starting the SFTP-inbox+Py3.6.1 with docker
docker run -it $* -d --hostname localhost     \
       -p 2222:22 --name ${CONTAINER}         \
       -v $INBOX:/home  \
       -v $LEGA:/root/ega \
       -v $CONF:/root/.lega/conf.ini  \
       ega-inbox

docker exec -it ${CONTAINER} bash -c "echo '$SSH_KEY' >> /etc/skel/.ssh/authorized_keys"
docker exec -it ${CONTAINER} pip install -e /root/ega
