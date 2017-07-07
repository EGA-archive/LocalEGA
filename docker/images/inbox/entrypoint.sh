#!/bin/bash

set -e

echo "$SSH_KEY" > /etc/ssh/authorized_keys/root # killing the file

pip install -e /root/ega
ega-inbox &
/usr/sbin/sshd -D -e
