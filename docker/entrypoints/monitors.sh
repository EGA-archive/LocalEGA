#!/bin/bash

set -e

pip install -e /root/ega

# sleep 6
# ega-monitor --sys &
# ega-monitor --user &

# wait
exec sleep 100000
