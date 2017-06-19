#!/bin/bash

set -e

pip install -e /root/ega

sleep 6
ega-inbox &

exec /usr/sbin/sshd -D -e
