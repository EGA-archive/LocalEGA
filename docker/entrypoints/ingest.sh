#!/bin/bash

set -e

pip3.6 install pgpy
pip3.6 install -e /root/ega

echo "Waiting for Message Broker"
until nc -4 --send-only ega_mq 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for database"
until nc -4 --send-only ega_db 5432 </dev/null &>/dev/null; do sleep 1; done

# echo "Waiting for Keyserver"
# until nc -4 --send-only ega_keys 9010 </dev/null &>/dev/null; do sleep 1; done

# echo "Starting the worker"
# exec ega-worker

exec sleep 10000000000
