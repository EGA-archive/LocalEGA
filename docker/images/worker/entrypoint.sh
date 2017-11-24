#!/bin/bash

set -e

# echo "Waiting for Keyserver"
until nc -4 --send-only ega_keys_$1 9010 </dev/null &>/dev/null; do sleep 1; done
echo "Starting the socket forwarder"
ega-socket-forwarder /root/.gnupg/S.gpg-agent ega_keys_$1:9010 --certfile /etc/ega/ssl.cert &

echo "Waiting for Central Message Broker"
until nc -4 --send-only cega_mq 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for Local Message Broker"
until nc -4 --send-only ega_mq_$1 5672 </dev/null &>/dev/null; do sleep 1; done

echo "Starting the ingestion worker"
exec ega-ingest
