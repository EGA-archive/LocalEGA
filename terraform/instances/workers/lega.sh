#!/bin/bash

set -e

mkdir -p ~/.gnupg && chmod 700 ~/.gnupg
mkdir -p ~/.rsa && chmod 700 ~/.rsa
mkdir -p ~/certs && chmod 700 ~/certs

unzip /tmp/gpg_public.zip -d ~/.gnupg
unzip /tmp/rsa_public.zip -d ~/.rsa
unzip /tmp/certs_public.zip -d ~/certs

rm /tmp/gpg_public.zip
rm /tmp/rsa_public.zip
rm /tmp/certs_public.zip

git clone -b terraform https://github.com/NBISweden/LocalEGA.git ~/repo
sudo pip3.6 install ~/repo/src

echo "Waiting for Message Broker"
until nc -4 --send-only ega-mq 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for database"
until nc -4 --send-only ega-db 5432 </dev/null &>/dev/null; do sleep 1; done


echo "Waiting for GPG and SSH agent"
until nc -4 --send-only ega-keys 9010 </dev/null &>/dev/null; do sleep 1; done
echo "Starting the gpg-agent forwarder"
ega-socket-forwarder ~/.gnupg/S.gpg-agent \
		     ega-keys:9010 \
		     --certfile ~/certs/selfsigned.cert &

echo "Starting the worker"
ega-worker &

echo "LEGA ready"
