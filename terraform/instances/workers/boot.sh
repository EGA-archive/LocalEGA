#!/bin/bash

set -e

# ========================
# No SELinux
echo "Disabling SElinux"
[ -f /etc/sysconfig/selinux ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/sysconfig/selinux
[ -f /etc/selinux/config ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/selinux/config
setenforce 0

# ================
echo "Mounting the staging area"
mkdir -p -m 0700 /ega
chown -R ega:ega /ega
mount -t nfs ega-inbox:/ega /ega || exit 1

echo "Updating the /etc/fstab for the staging area"
sed -i -e '/ega-inbox:/ d' /etc/fstab
echo "ega-inbox:/ega /ega  nfs   auto,noatime,nolock,bg,nfsvers=4,intr,tcp,actimeo=1800 0 0" >> /etc/fstab

#########################################
# Code
#########################################
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

cat > /etc/systemd/system/ega-worker.service <<'EOF'
[Unit]
Description=EGA Worker service
After=syslog.target
After=network.target

After=ega-socket-forwarder.service
BindsTo=ega-socket-forwarder.service

[Service]
Slice=ega.slice
Type=simple
User=root
Group=root
EnvironmentFile=/etc/ega/options

ExecStart=/bin/ega-worker $EGA_OPTIONS

StandardOutput=syslog
StandardError=syslog

Restart=on-failure
RestartSec=10
TimeoutSec=600

Sockets=ega-db.socket ega-mq.socket

[Install]
WantedBy=multi-user.target
EOF

##################################################

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

##################################################

cat > /etc/systemd/system/ega-socket-forwarder@.socket <<EOF
[Unit]
Description=EGA GPG-agent socket activation
After=syslog.target
After=network.target

[Socket]
ListenStream=/run/ega/S.gpg-agent
SocketUser=ega
SocketGroup=ega
SocketMode=0600
DirectoryMode=0755

[Install]
WantedBy=sockets.target
EOF

cat > ~ega/.gnupg/S.gpg-agent <<EOF
%Assuan%
socket=/run/ega/S.gpg-agent
EOF
chown ega:ega ~ega/.gnupg/S.gpg-agent
chmod 600 ~ega/.gnupg/S.gpg-agent


cat > /etc/systemd/system/ega-socket-forwarder@.service <<'EOF'
[Unit]
Description=EGA Socket forwarding service (to %I)
After=syslog.target
After=network.target

Requires=ega-socket-forwarder@.socket

[Service]
Slice=ega.slice
Type=simple
User=ega
Group=ega
ExecStart=/bin/ega-socket-forwarder /run/ega/S.gpg-agent %i --certfile $EGA_GPG_CERTFILE

Environment=EGA_GPG_CERTFILE=~/.certs/selfsigned.cert

Restart=on-failure
RestartSec=10
TimeoutSec=600

Sockets=ega-socket-forwarder@.socket

[Install]
WantedBy=multi-user.target
EOF

echo "Starting the gpg-agent forwarder"
systemctl start ega-socket-forwarder@ega-keys:9010.service

echo "Starting the worker"
systemctl start ega-worker.service

echo "Enabling services"
systemctl enable ega-socket-forwarder@ega-keys:9010.service
systemctl enable ega-worker.service

echo "Workers ready"
