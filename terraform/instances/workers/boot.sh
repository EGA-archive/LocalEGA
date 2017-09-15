#!/bin/bash

set -e

# ========================
# No SELinux
echo "Disabling SElinux"
[ -f /etc/sysconfig/selinux ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/sysconfig/selinux
[ -f /etc/selinux/config ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/selinux/config
setenforce 0

#########################################
# Code
#########################################
git clone -b terraform https://github.com/NBISweden/LocalEGA.git ~/repo
pip3.6 install ~/repo/src

mkdir -p ~ega/.gnupg && chmod 700 ~ega/.gnupg
mkdir -p ~ega/.rsa && chmod 700 ~ega/.rsa
mkdir -p ~ega/.certs && chmod 700 ~ega/.certs

unzip /tmp/gpg.zip -d ~ega/.gnupg
unzip /tmp/rsa.zip -d ~ega/.rsa
unzip /tmp/certs.zip -d ~ega/.certs

chown -R ega:ega ~ega/.gnupg
chown -R ega:ega ~ega/.rsa
chown -R ega:ega ~ega/.certs

rm /tmp/gpg.zip
rm /tmp/rsa.zip
rm /tmp/certs.zip

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

# Cloud init should run late enough, so that /run/user/1001 exists
EGA_SOCKET=$(su -c "gpgconf --list-dirs agent-socket" - ega) # as ega user

cat > /etc/systemd/system/ega-socket-forwarder.socket <<EOF
[Unit]
Description=GPG-agent socket activation
After=syslog.target
After=network.target

[Socket]
ListenStream=$EGA_SOCKET
SocketUser=ega
SocketGroup=ega
SocketMode=0600
ExecStartPre=/usr/bin/su - ega -c "gpgconf --create-socketdir"

[Install]
WantedBy=sockets.target
EOF

cat > /etc/systemd/system/ega-socket-forwarder.service <<EOF
[Unit]
Description=EGA Socket forwarding service (to GPG-master on port 9010)
After=syslog.target
After=network.target
After=user.slice systemd-logind.service

Requires=ega-socket-forwarder.socket
After=ega-socket-forwarder.socket

[Service]
Slice=ega.slice
Type=simple
User=ega
Group=ega
ExecStart=/bin/ega-socket-forwarder $EGA_SOCKET ega-keys:9010 --certfile \$EGA_GPG_CERTFILE
RuntimeDirectory=ega
Environment=EGA_GPG_CERTFILE=~/.certs/selfsigned.cert

Restart=on-failure
RestartSec=10
TimeoutSec=600

Sockets=ega-socket-forwarder.socket

[Install]
WantedBy=ega-worker.service
RequiredBy=ega-worker.service
EOF

cat > /etc/systemd/system/ega-worker.service <<EOF
[Unit]
Description=EGA Worker service
After=syslog.target
After=network.target

After=ega-socket-forwarder.socket
BindsTo=ega-socket-forwarder.socket

[Service]
Slice=ega.slice
Type=simple
User=ega
Group=ega
EnvironmentFile=/etc/ega/options
ExecStart=/bin/ega-worker \$EGA_OPTIONS

StandardOutput=syslog
StandardError=syslog

Restart=on-failure
RestartSec=10
TimeoutSec=600

[Install]
WantedBy=multi-user.target
EOF

# ================
echo "Mounting the staging area"
mkdir -p -m 0700 /ega
chown -R ega:ega /ega
mount -t nfs ega-inbox:/ega /ega || exit 1

echo "Updating the /etc/fstab for the staging area"
sed -i -e '/ega-inbox:/ d' /etc/fstab
echo "ega-inbox:/ega /ega  nfs  noauto,x-systemd.automount,x-systemd.device-timeout=10,timeo=14,x-systemd.idle-timeout=1min 0 0" >> /etc/fstab
# AutoMount points will be created after reboot

# ================
# echo "Starting the worker"
# systemctl start ega-worker.service ega-socket-forwarder.service ega-socket-forwarder.socket

echo "Enabling the ega user to linger"
loginctl enable-linger ega

echo "Enabling services"
systemctl enable ega-worker.service ega-socket-forwarder.service ega-socket-forwarder.socket


echo "Workers ready"
echo "Rebooting"
systemctl reboot
