#!/bin/bash

set -e

pip3.6 install pgpy dill
pip3.6 install -e /root/ega

echo "Starting the key management server"
#exec ega-keyserver --keys /etc/ega/keys.ini

exec sleep 1110000000000
