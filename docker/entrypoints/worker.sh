#!/bin/bash

set -e

pip install -e /root/ega

echo "Waiting for Message Broker"
until nc -4 --send-only ega_mq 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for database"
until nc -4 --send-only ega_db 5432 </dev/null &>/dev/null; do sleep 1; done

echo "Waiting for GPG and SSH agent"
until nc -4 --send-only ega_keys 9010 </dev/null &>/dev/null; do sleep 1; done

echo "Starting the gpg-agent forwarder"
ega-socket-forwarder /root/.gnupg/S.gpg-agent \
		     ega_keys:9010 \
		     --certfile /etc/ega/ega.cert &
    		     #--log /root/ega/lega/conf/loggers/debug.yaml &

echo "Starting the worker"
exec ega-worker
