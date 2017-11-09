#!/bin/bash

set -e

cp -r /root/ega /root/run
pip3.6 install /root/run

echo "Waiting for Central Message Broker"
until nc -4 --send-only cega_mq 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for Local Message Broker"
until nc -4 --send-only ega_mq_$1 5672 </dev/null &>/dev/null; do sleep 1; done

echo "Starting the verifier"
ega-verify &

echo "Starting the vault listener"
exec ega-vault
