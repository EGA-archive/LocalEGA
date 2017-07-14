#!/bin/bash

set -e

python /usr/local/lib/python2.7/dist-packages/pgadmin4/pgAdmin4.py &

exec /usr/local/bin/docker-entrypoint.sh postgres
