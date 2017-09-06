#!/bin/bash

set -e

pip install -e /root/ega

echo "Waiting for Message Broker"
until nc -4 --send-only ega-mq 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for database"
until nc -4 --send-only ega-db 5432 </dev/null &>/dev/null; do sleep 1; done

# CentralEGA to LocalEGA

ega-connect "cega:lega:files"  &
ega-connect "cega:lega:users"  &

# LocalEGA to CentralEGA

ega-connect "lega:cega:files"  &
ega-connect "lega:cega:users"  &

wait

