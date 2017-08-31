#!/bin/bash

set -e

git clone -b terraform https://github.com/NBISweden/LocalEGA.git ~/repo
pip3.6 install ~/repo/src

#########################################
# Systemd files
#########################################
cat > /etc/ega/options <<EOF
EGA_OPTIONS=""
EOF

cat > /etc/systemd/system/ega.slice <<EOF
[Unit]
Description=EGA Slice
DefaultDependencies=no
Before=slices.target

#[Slice]
#CPUShares=512
#MemoryLimit=2G
EOF

cat > /etc/systemd/system/ega-db.socket <<EOF
[Unit]
Description=EGA Database socket activation
After=syslog.target
After=network.target

[Socket]
ListenStream=ega-db:5432

[Install]
WantedBy=sockets.target
EOF

cat > /etc/systemd/system/ega-mq.socket <<EOF
[Unit]
Description=EGA Message Broker socket activation
After=syslog.target
After=network.target

[Socket]
ListenStream=ega-mq:5672

[Install]
WantedBy=sockets.target
EOF

cat > /etc/systemd/system/ega-frontend.service <<'EOF'
[Unit]
Description=EGA Frontend service
After=syslog.target
After=network.target

[Service]
Slice=ega.slice
Type=simple
User=root
Group=root
EnvironmentFile=/etc/ega/options

ExecStart=/bin/ega-frontend $EGA_OPTIONS

StandardOutput=syslog
StandardError=syslog

Restart=on-failure
RestartSec=10
TimeoutSec=600

Sockets=ega-db.socket ega-mq.socket

[Install]
WantedBy=multi-user.target
EOF


echo "Starting the frontend"
systemctl start ega-frontend
systemctl enable ega-frontend

echo "EGA Frontend ready"
