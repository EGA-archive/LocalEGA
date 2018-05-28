#!/bin/bash

set -e

# MQ_INSTANCE env must be defined
[[ -z "$MQ_INSTANCE" ]] && echo 'Environment MQ_INSTANCE is empty' 1>&2 && exit 1

# Changing permissions
echo "Changing permissions for /ega/vault and /ega/staging"
chown lega:lega /ega/vault /ega/staging
chmod 750 /ega/vault /ega/staging
chmod g+s /ega/vault /ega/staging # setgid bit

echo "Waiting for Local Message Broker"
until nc -4 --send-only ${MQ_INSTANCE} 5672 </dev/null &>/dev/null; do sleep 1; done

echo "Starting the verifier"
gosu lega ega-verify &

echo "Starting the vault listener"
exec gosu lega ega-vault
