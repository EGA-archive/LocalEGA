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
ListenStream=ega-mq:5432

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

EGA_SOCKET=$(su -c "gpgconf --list-dirs agent-socket" - ega) # as ega user

cat > /etc/systemd/system/ega-socket-forwarder.service <<EOF
[Unit]
Description=EGA Socket forwarding service (to GPG-master on port 9010)
After=syslog.target
After=network.target

[Service]
Slice=ega.slice
Type=simple
User=ega
Group=ega
ExecStartPre=-/bin/rm -f ${EGA_SOCKET}
ExecStart=/bin/ega-socket-forwarder ${EGA_SOCKET} '192.168.10.12:9010' --certfile \$EGA_GPG_CERTFILE

Environment=EGA_GPG_CERTFILE=~/.certs/selfsigned.cert

Restart=on-failure
RestartSec=10
TimeoutSec=600

[Install]
WantedBy=multi-user.target
EOF

echo "Starting the gpg-agent forwarder"
systemctl start ega-socket-forwarder.service

echo "Starting the worker"
systemctl start ega-worker.service

echo "Enabling services"
systemctl enable ega-socket-forwarder.service
systemctl enable ega-worker.service

echo "Workers ready"
