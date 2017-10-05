#!/bin/bash

set -e

git clone -b docker https://github.com/NBISweden/LocalEGA.git ~/repo
pip3.6 install ~/repo/src

echo "Waiting for Central Message Broker"
until nc -4 --send-only cega_mq 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for Local Message Broker"
until nc -4 --send-only ega_mq 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for database"
until nc -4 --send-only ega_db 5432 </dev/null &>/dev/null; do sleep 1; done

echo "Starting the verifier"
ega-verify &

echo "Starting the vault listener"
exec ega-vault
