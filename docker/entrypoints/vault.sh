#!/bin/bash

set -e

pip install -e /root/ega

echo "Waiting for Message Broker"
until nc -4 --send-only ega_mq 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for database"
until nc -4 --send-only ega_db 5432 </dev/null &>/dev/null; do sleep 1; done

echo "Starting the verifier"
ega-verify &

echo "Starting the vault listener"
exec ega-vault
