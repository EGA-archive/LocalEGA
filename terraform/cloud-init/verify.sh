#!/bin/bash

set -e

pip install -e /root/ega

echo "Waiting for Message Broker"
until nc -4 --send-only ega-mq 5672 </dev/null &>/dev/null; do sleep 1; done

echo "Starting the verifier"
exec ega-verify
