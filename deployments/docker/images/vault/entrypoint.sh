#!/bin/bash

set -e

# MQ_INSTANCE env must be defined
[[ -z "$MQ_INSTANCE" ]] && echo 'Environment MQ_INSTANCE is empty' 1>&2 && exit 1

echo "Waiting for Local Message Broker"
until nc -4 --send-only ${MQ_INSTANCE} 5672 </dev/null &>/dev/null; do sleep 1; done

echo "Starting the verifier"
ega-verify &

echo "Starting the vault listener"
exec ega-vault
