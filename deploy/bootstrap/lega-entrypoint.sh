#!/bin/sh
set -e

if ! test -e /etc/ega/ssl.key.lega; then
    cp /etc/ega/ssl.key /etc/ega/ssl.key.lega
    chmod 400 /etc/ega/ssl.key.lega
fi

exec $@
