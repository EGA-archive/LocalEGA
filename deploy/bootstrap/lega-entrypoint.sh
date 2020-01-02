#!/bin/sh
set -e

cp /etc/ega/ssl.key /etc/ega/ssl.key.lega
chmod 400 /etc/ega/ssl.key.lega

exec $@
