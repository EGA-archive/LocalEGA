#!/bin/bash

set -e

the_trap () {
  [[ -z "$INSTANCE" ]] && INST="anonymous" || INST=$INSTANCE
  if [[ -z "$2" ]]; then
    curl -d '{"instance":"'"$INST"'", "service":"lega-ingest", "status": "'"$1"'"}' -H "Content-Type: application/json" -X POST http://${MONITOR}:5039/status &>/dev/null
  else
    curl -d '{"instance":"'"$INST"'", "service":"lega-ingest", "status": "'"$1"'", "exitStatus" : "'"$2"'"}' -H "Content-Type: application/json" -X POST http://${MONITOR}:5039/status &>/dev/null
  fi
}

# MQ_INSTANCE, KEYSERVER_HOST and KEYSERVER_PORT env must be defined
[[ -z "$CEGA_INSTANCE" ]] && echo 'Environment CEGA_INSTANCE is empty' 1>&2 && the_trap 'stopped' 1 && exit 1
[[ -z "$MQ_INSTANCE" ]] && echo 'Environment MQ_INSTANCE is empty' 1>&2 && the_trap 'stopped' 1 && exit 1
[[ -z "$KEYSERVER_HOST" ]] && echo 'Environment KEYSERVER_HOST is empty' 1>&2 && the_trap 'stopped' 1 && exit 1
[[ -z "$KEYSERVER_PORT" ]] && echo 'Environment KEYSERVER_PORT is empty' 1>&2 && the_trap 'stopped' 1 && exit 1

the_trap 'started'

# echo "Waiting for Keyserver"
until nc -4 --send-only ${KEYSERVER_HOST} ${KEYSERVER_PORT} </dev/null &>/dev/null; do sleep 1; done
echo "Starting the socket forwarder"
ega-socket-forwarder /root/.gnupg/S.gpg-agent ${KEYSERVER_HOST}:${KEYSERVER_PORT} --certfile /etc/ega/ssl.cert &

echo "Waiting for Central Message Broker"
until nc -4 --send-only ${CEGA_INSTANCE} 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for Local Message Broker"
until nc -4 --send-only ${MQ_INSTANCE} 5672 </dev/null &>/dev/null; do sleep 1; done

ingest () {
  echo "Starting the ingestion worker"
  exec ega-ingest
}

trap 'the_trap "stopped" $?' TERM INT
ingest &
PID=$!
wait $PID
