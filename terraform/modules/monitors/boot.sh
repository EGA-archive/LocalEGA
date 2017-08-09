#!/bin/bash

set -e

pip install -e /root/ega

echo "Waiting for database"
until nc -4 --send-only ega-db 5432 </dev/null &>/dev/null; do sleep 1; done
# ega-monitor --sys &
# ega-monitor --user &

# wait
exec sleep 100000
