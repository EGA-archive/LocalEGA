#!/bin/bash

set -e

git clone https://github.com/NBISweden/LocalEGA.git ~/repo
sudo pip3.6 install ~/repo/src

echo "Waiting for database"
until nc -4 --send-only ega-db 5432 </dev/null &>/dev/null; do sleep 1; done
# ega-monitor --sys &
# ega-monitor --user &
