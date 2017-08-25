#!/bin/bash

set -e

git clone -b terraform https://github.com/NBISweden/LocalEGA.git ~/repo
sudo pip3.6 install ~/repo/src

echo "Waiting for database"
until nc -4 --send-only ega-db 5432 </dev/null &>/dev/null; do sleep 1; done
# ega-monitor --sys &
# ega-monitor --user &


sudo bash <<'EOF'
cat > /etc/rsyslog.d/50-ega.conf <<LOGEOF
local1.* /var/log/ega.log
LOGEOF
systemctl restart rsyslog
EOF
