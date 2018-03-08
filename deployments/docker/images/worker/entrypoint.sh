#!/bin/bash

set -e

# MQ_INSTANCE and KEYSERVER_INSTANCE env must be defined
[[ -z "$MQ_INSTANCE" ]] && echo 'Environment MQ_INSTANCE is empty' 1>&2 && exit 1
[[ -z "$KEYSERVER_INSTANCE" ]] && echo 'Environment KEYSERVER_INSTANCE is empty' 1>&2 && exit 1

echo "Waiting for Keyserver"
until nc -4 --send-only ${KEYSERVER_INSTANCE} 443 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for Local Message Broker"
until nc -4 --send-only ${MQ_INSTANCE} 5672 </dev/null &>/dev/null; do sleep 1; done

echo "Starting the ingestion worker"
exec ega-ingest
