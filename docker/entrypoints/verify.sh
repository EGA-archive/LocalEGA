#!/bin/bash

set -e

pip install -e /root/ega
while ! nc -4 --send-only ega-mq 5672 </dev/null &>/dev/null; do sleep 1; done
exec ega-verify
