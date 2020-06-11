#!/bin/sh
set -e

cp -f /etc/ega/ssl.key /etc/ega/ssl.key.lega
chmod 400 /etc/ega/ssl.key.lega

exec $@
