#!/bin/bash

set -e

pip install -e /root/ega
echo "Waiting for Message Broker"
until nc -4 --send-only ega-mq 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for database"
until nc -4 --send-only ega-db 5432 </dev/null &>/dev/null; do sleep 1; done

echo "Starting the inbox listener"
ega-inbox &

echo "Starting the SFTP server"
exec /usr/sbin/sshd -D -e
