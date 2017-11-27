#!/bin/bash

set -e

# MQ_INSTANCE, KEYSERVER_HOST and KEYSERVER_PORT env must be defined
[[ -z "$MQ_INSTANCE" ]] && echo 'Environment MQ_INSTANCE is empty' 1>&2 && exit 1
[[ -z "$KEYSERVER_HOST" ]] && echo 'Environment KEYSERVER_HOST is empty' 1>&2 && exit 1
[[ -z "$KEYSERVER_PORT" ]] && echo 'Environment KEYSERVER_PORT is empty' 1>&2 && exit 1

# echo "Waiting for Keyserver"
until nc -4 --send-only ${KEYSERVER_HOST} ${KEYSERVER_PORT} </dev/null &>/dev/null; do sleep 1; done
echo "Starting the socket forwarder"
ega-socket-forwarder /root/.gnupg/S.gpg-agent ${KEYSERVER_HOST}:${KEYSERVER_PORT} --certfile /etc/ega/ssl.cert &

echo "Waiting for Central Message Broker"
until nc -4 --send-only cega_mq 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for Local Message Broker"
until nc -4 --send-only ${MQ_INSTANCE} 5672 </dev/null &>/dev/null; do sleep 1; done

echo "Starting the ingestion worker"
exec ega-ingest
