#!/bin/bash

set -e

cat /root/.ssh/ega.pub >> /root/.ssh/authorized_keys && \
chmod 600 /root/.ssh/authorized_keys

pip install -e /root/ega
echo "Waiting for Message Broker"
until nc -4 --send-only ega-mq 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for database"
until nc -4 --send-only ega-db 5432 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for gpg-agent"
until nc -4 --send-only ega-keys 22 </dev/null &>/dev/null; do sleep 1; done

echo "Starting the worker"
ega-worker &

# Absolute path to version 7.5
exec /usr/local/sbin/sshd -4 -D -e

