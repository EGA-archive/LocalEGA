#!/bin/bash

set -e

git clone https://github.com/NBISweden/LocalEGA.git ~/ega
pip3.6 install ~/ega/src

echo "Waiting for database"
until nc -4 --send-only ega-db 5432 </dev/null &>/dev/null; do sleep 1; done

echo "Starting the frontend"
ega-frontend &
