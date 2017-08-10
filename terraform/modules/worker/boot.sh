#!/bin/bash

set -e

git clone https://github.com/NBISweden/LocalEGA.git ~/ega
sudo pip3.6 install PyYaml Markdown
sudo pip3.6 install -e ~/ega/src

echo "Waiting for Message Broker"
until nc -4 --send-only ega-mq 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for database"
until nc -4 --send-only ega-db 5432 </dev/null &>/dev/null; do sleep 1; done

echo "Waiting for GPG and SSH agent"
until nc -4 --send-only ega-keys 9010 </dev/null &>/dev/null; do sleep 1; done
echo "Starting the gpg-agent forwarder"
ega-socket-forwarder /root/.gnupg/S.gpg-agent \
		     ega-keys:9010 \
		     --certfile /etc/ega/ega.cert &
    		     #--log /root/ega/lega/conf/loggers/debug.yaml &

echo "Starting the worker"
ega-worker &
