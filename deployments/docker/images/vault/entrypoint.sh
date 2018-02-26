#!/bin/bash

set -e

the_trap () {
  [[ -z "$INSTANCE" ]] && INST="anonymous" || INST=$INSTANCE
  if [[ -z "$2" ]]; then
    curl -d '{"instance":"'"$INST"'", "service":"lega-vault", "status": "'"$1"'"}' -H "Content-Type: application/json" -X POST http://${MONITOR}:5039/status &>/dev/null
  else
    curl -d '{"instance":"'"$INST"'", "service":"lega-vault", "status": "'"$1"'", "exitStatus" : "'"$2"'"}' -H "Content-Type: application/json" -X POST http://${MONITOR}:5039/status &>/dev/null
  fi
}

# MQ_INSTANCE env must be defined
[[ -z "$MQ_INSTANCE" ]] && echo 'Environment MQ_INSTANCE is empty' 1>&2 && the_trap 'stopped' 1 && exit 1
[[ -z "$CEGA_INSTANCE" ]] && echo 'Environment CEGA_INSTANCE is empty' 1>&2 && the_trap 'stopped' 1 && exit 1

the_trap 'started'

echo "Waiting for Central Message Broker"
until nc -4 --send-only ${CEGA_INSTANCE} 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for Local Message Broker"
until nc -4 --send-only ${MQ_INSTANCE} 5672 </dev/null &>/dev/null; do sleep 1; done

echo "Starting the verifier"
ega-verify &

vault_process() {
  echo "Starting the vault listener"
  ega-vault
}

trap 'the_trap "stopped" $?' TERM INT
vault_process &
PID=$!
wait $PID
