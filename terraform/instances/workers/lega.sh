#!/bin/bash

set -e

mkdir -p ~/.gnupg && chmod 700 ~/.gnupg
mkdir -p ~/.rsa && chmod 700 ~/.rsa
mkdir -p ~/certs && chmod 700 ~/certs

unzip /tmp/gpg.zip -d ~/.gnupg
unzip /tmp/rsa.zip -d ~/.rsa
unzip /tmp/certs.zip -d ~/certs

rm /tmp/gpg.zip
rm /tmp/rsa.zip
rm /tmp/certs.zip

git clone -b terraform https://github.com/NBISweden/LocalEGA.git ~/repo
sudo pip3.6 install ~/repo/src

echo "Waiting for Message Broker"
until /bin/nc -4 --send-only ega-mq 5672 </dev/null &>/dev/null; do /bin/sleep 1; done
echo "Waiting for database"
until /bin/nc -4 --send-only ega-db 5432 </dev/null &>/dev/null; do /bin/sleep 1; done
echo "Waiting for GPG and SSH agent"
until /bin/nc -4 --send-only ega-keys 9010 </dev/null &>/dev/null; do /bin/sleep 1; done

echo "Starting the gpg-agent forwarder"
systemctl start ega-socket-forwarder
systemctl enable ega-socket-forwarder

echo "Starting the worker"
systemctl start ega-worker
systemctl enable ega-worker

echo "LEGA ready"
