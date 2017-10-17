#!/bin/bash

set -e

cmd="$@"
SLEEPTIME=1
RETRIES=30

export PGPASSWORD=${POSTGRES_PASSWORD}

until psql -U ${POSTGRES_USER} -h ega_db -c "select 1" || [ ${RETRIES} -eq 0 ]; do
    echo "Waiting for Postgres server, $((RETRIES--)) remaining attempts..."
    sleep ${SLEEPTIME}
done

if ! psql -U ${POSTGRES_USER} -h ega_db -c "select 1"; then
    exit 1
fi

>&2 echo "Postgres is up - executing command"
exec $cmd
