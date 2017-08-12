#!/bin/bash

set -e

unzip /tmp/gpg.zip -d /root/.gnupg && \
rm /tmp/gpg.zip

mkdir -p -m 0700 /root/.rsa && \
unzip /tmp/rsa.zip -d /root/.rsa && \
rm /tmp/rsa.zip

mkdir -p -m 0700 /etc/ega && \
unzip /tmp/certs.zip -d /etc/ega && \
rm /tmp/certs.zip

git clone https://github.com/NBISweden/LocalEGA.git ~/ega
pip3.6 install -e ~/ega/src

echo "Waiting for Message Broker"
until nc -4 --send-only ega-mq 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for database"
until nc -4 --send-only ega-db 5432 </dev/null &>/dev/null; do sleep 1; done

echo "Waiting for GPG and SSH agent"
until nc -4 --send-only ega-keys 9010 </dev/null &>/dev/null; do sleep 1; done
echo "Starting the gpg-agent forwarder"
ega-socket-forwarder /root/.gnupg/S.gpg-agent \
		     ega-keys:9010 \
		     --certfile /etc/ega/selfsigned.cert &

echo "Starting the worker"
ega-worker &
