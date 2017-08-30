#!/bin/bash

set -e

git clone -b terraform https://github.com/NBISweden/LocalEGA.git ~/repo
sudo pip3.6 install ~/repo/src

echo "Waiting for Message Broker"
until nc -4 --send-only ega-mq 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for database"
until nc -4 --send-only ega-db 5432 </dev/null &>/dev/null; do sleep 1; done

sudo systemctl start ega-connector@cega:lega:files.service
sudo systemctl start ega-connector@cega:lega:users.service
sudo systemctl start ega-connector@lega:cega:files.service
sudo systemctl start ega-connector@lega:cega:users.service

sudo systemctl enable ega-connector@cega:lega:files.service
sudo systemctl enable ega-connector@cega:lega:users.service
sudo systemctl enable ega-connector@lega:cega:files.service
sudo systemctl enable ega-connector@lega:cega:users.service

echo "LEGA ready"
