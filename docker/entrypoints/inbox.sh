#!/bin/bash

set -e

sleep 6

pip install -e /root/ega
ega-inbox &

exec /usr/sbin/sshd -D -e
