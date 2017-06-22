#!/bin/bash

set -e

pip install -e /root/ega
pkill gpg-agent || true
# Start the GPG Agent in /root/.gnupg
/usr/local/bin/gpg-agent --daemon

echo "Waiting for Message Broker"
until nc -4 --send-only ega-mq 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for database"
until nc -4 --send-only ega-db 5432 </dev/null &>/dev/null; do sleep 1; done


KEYGRIP=$(gpg2 --fingerprint --fingerprint ega@nbis.se | grep fingerprint | tail -1 | cut -d= -f2 | sed -e 's/ //g')
/usr/local/libexec/gpg-preset-passphrase --preset -P $GPG_PASSPHRASE $KEYGRIP
unset GPG_PASSPHRASE

echo "Starting the worker"
exec ega-worker
