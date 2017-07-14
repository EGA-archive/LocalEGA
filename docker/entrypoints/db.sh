#!/bin/bash

set -e

( # new shell
    workon pgadmin4
    python /usr/local/lib/python2.7/dist-packages/pgadmin4/pgAdmin4.py
) &

exec /usr/local/bin/docker-entrypoint.sh postgres
