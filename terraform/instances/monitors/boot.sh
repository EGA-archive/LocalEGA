#!/bin/bash

set -e

git clone -b terraform https://github.com/NBISweden/LocalEGA.git ~/repo
sudo pip3.6 install ~/repo/src

echo "Waiting for database"
until nc -4 --send-only ega-db 5432 </dev/null &>/dev/null; do sleep 1; done
# ega-monitor --sys &
# ega-monitor --user &


sudo tee /etc/rsyslog.d/ega.conf <<'EOF'
# for UDP use:
module(load="imudp") # needs to be done just once 
input(type="imudp" port="10514")
#$ModLoad imudp
#$InputUDPServerRun 10514

local1.* /var/log/ega.log
EOF

sudo systemctl restart rsyslog

echo "LEGA ready"
