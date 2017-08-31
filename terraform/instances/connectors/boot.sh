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

cat > /etc/systemd/system/ega-connector@.service <<'EOF'
[Unit]
Description=EGA Connector service (%I)
After=syslog.target
After=network.target

[Service]
Slice=ega.slice
Type=simple
User=ega
Group=ega
EnvironmentFile=/etc/ega/options

# CentralEGA to LocalEGA
ExecStart=/bin/ega-connect $EGA_OPTIONS %i

StandardOutput=syslog
StandardError=syslog

Restart=on-failure
RestartSec=10
TimeoutSec=600

Sockets=ega-db.socket ega-mq.socket

[Install]
WantedBy=multi-user.target
EOF

#########################################
# Start the connectors
#########################################

systemctl restart ega-connector@cega:lega:files.service
systemctl restart ega-connector@cega:lega:users.service
systemctl restart ega-connector@lega:cega:files.service
systemctl restart ega-connector@lega:cega:users.service

systemctl enable ega-connector@cega:lega:files.service
systemctl enable ega-connector@cega:lega:users.service
systemctl enable ega-connector@lega:cega:files.service
systemctl enable ega-connector@lega:cega:users.service

echo "EGA Connectors ready"
