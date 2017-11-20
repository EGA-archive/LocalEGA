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

cat > /etc/systemd/system/ega-vault.service <<'EOF'
[Unit]
Description=EGA Vault service
After=syslog.target
After=network.target

[Service]
Slice=ega.slice
Type=simple
User=root
Group=root
EnvironmentFile=/etc/ega/options

ExecStart=/bin/ega-vault $EGA_OPTIONS

StandardOutput=syslog
StandardError=syslog

Restart=on-failure
RestartSec=10
TimeoutSec=600

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/ega-verify.service <<'EOF'
[Unit]
Description=EGA Verifier service
After=syslog.target
After=network.target

[Service]
Slice=ega.slice
Type=simple
User=root
Group=root
EnvironmentFile=/etc/ega/options

ExecStart=/bin/ega-verify $EGA_OPTIONS

StandardOutput=syslog
StandardError=syslog

Restart=on-failure
RestartSec=10
TimeoutSec=600

[Install]
WantedBy=multi-user.target
EOF

# Will systemd restart the processes because they could not contact
# the database and message broker?

echo "Starting the verifier"
systemctl start ega-verify
systemctl enable ega-verify

echo "Starting the vault listener"
systemctl start ega-vault
systemctl enable ega-vault

echo "Vault and Verifier ready"
