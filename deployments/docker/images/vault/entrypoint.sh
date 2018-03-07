#!/bin/bash

set -e

# MQ_INSTANCE env must be defined
[[ -z "$MQ_INSTANCE" ]] && echo 'Environment MQ_INSTANCE is empty' 1>&2 && exit 1
[[ -z "$CEGA_INSTANCE" ]] && echo 'Environment CEGA_INSTANCE is empty' 1>&2 && exit 1

echo "Waiting for Central Message Broker"
until nc -4 -z ${CEGA_INSTANCE} 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for Local Message Broker"
until nc -4 -z ${MQ_INSTANCE} 5672 </dev/null &>/dev/null; do sleep 1; done

echo "Starting the verifier"
ega-verify &

echo "Starting the vault listener"
exec ega-vault
