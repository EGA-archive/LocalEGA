#!/bin/bash

set -e

pip install -e /root/ega

cat /root/.ssh/ega.pub >> /root/.ssh/authorized_keys && \
chmod 600 /root/.ssh/authorized_keys

echo "Starting the SSH server in detached mode"
/usr/local/sbin/sshd -4 -e # Absolute path to version 7.5

echo "Waiting for Message Broker"
until nc -4 --send-only ega-mq 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for database"
until nc -4 --send-only ega-db 5432 </dev/null &>/dev/null; do sleep 1; done

echo "Starting the worker"
exec ega-worker
