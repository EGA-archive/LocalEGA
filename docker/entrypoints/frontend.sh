#!/bin/bash

set -e

pip install -e /root/ega

echo "Waiting for database"
until nc -4 --send-only ega_db 5432 </dev/null &>/dev/null; do sleep 1; done

echo "Starting the frontend"
exec ega-frontend
