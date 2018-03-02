#!/bin/bash

set -e

# KEYSERVER_PORT env must be defined
[[ -z "$KEYSERVER_PORT" ]] && echo 'Environment KEYSERVER_PORT is empty' 1>&2 && exit 1

echo "Starting the key management server"
exec ega-keyserver --keys /etc/ega/keys.ini
