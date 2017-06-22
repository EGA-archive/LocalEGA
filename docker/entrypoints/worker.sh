#!/bin/bash

set -e

pip install -e /root/ega

chmod 700 /root/.gnupg

pkill gpg-agent || true
# Start the GPG Agent in /root/.gnupg
/usr/local/bin/gpg-agent --daemon

KEYGRIP=$(gpg2 -k --with-keygrip ega@nbis.se | awk '/Keygrip/{print $3;exit;}')
/usr/local/libexec/gpg-preset-passphrase --preset -P $GPG_PASSPHRASE $KEYGRIP
unset GPG_PASSPHRASE

echo "Waiting for Message Broker"
until nc -4 --send-only ega-mq 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for database"
until nc -4 --send-only ega-db 5432 </dev/null &>/dev/null; do sleep 1; done

echo "Starting the worker"
exec ega-worker
