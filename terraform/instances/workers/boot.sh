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

cat > /etc/systemd/system/ega-socket-forwarder.socket <<EOF
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

cat > /etc/systemd/system/ega-socket-forwarder.service <<'EOF'
[Unit]
Description=EGA Socket forwarding service (to GPG-master on port 9010)
After=syslog.target
After=network.target

Requires=ega-socket-forwarder.socket
After=ega-socket-forwarder.socket

[Service]
Slice=ega.slice
Type=simple
User=ega
Group=ega
ExecStart=/bin/ega-socket-forwarder /run/ega/S.gpg-agent ega-keys:9010 --certfile $EGA_GPG_CERTFILE

Environment=EGA_GPG_CERTFILE=~/.certs/selfsigned.cert

Restart=on-failure
RestartSec=10
TimeoutSec=600

Sockets=ega-socket-forwarder.socket

[Install]
WantedBy=ega-worker.service
RequiredBy=ega-worker.service
EOF

# To be run as EGA user
cat > /usr/local/bin/ega_create_socket_link.sh <<'EOF'
#!/bin/bash
[[ $# -ne 1 ]] && echo "Specify one argument (only): Bailing out..." && exit 1
EGA_GPG_SOCKET=$(gpgconf --list-dirs $1-socket)
[[ -z "$EGA_GPG_SOCKET" ]] && echo "We couldn't find the gpg socket location: Bailing out..." && exit 2
[[ -f "$EGA_GPG_SOCKET" ]] && echo "GPG socket link already in $EGA_GPG_SOCKET" && exit 0
# otherwise, create the file
mkdir -p $(dirname $EGA_GPG_SOCKET)
cat > $EGA_GPG_SOCKET <<EOFSOCKET
%Assuan%
socket=/run/ega/S.gpg-$1
EOFSOCKET
#chown ega:ega $EGA_GPG_SOCKET
chmod 600 $EGA_GPG_SOCKET
echo "GPG socket link created (see $EGA_GPG_SOCKET)"
EOF
chown ega:ega /usr/local/bin/ega_create_socket_link.sh
chmod 700 /usr/local/bin/ega_create_socket_link.sh

cat > /etc/systemd/system/ega-worker.service <<EOF
[Unit]
Description=EGA Worker service
After=syslog.target
After=network.target

After=ega-socket-forwarder.socket
BindsTo=ega-socket-forwarder.socket

# For the runtime directory to be correctly set
After=systemd-logind.service
After=user@$(id -u ega).service

[Service]
Slice=ega.slice
Type=simple
User=ega
Group=ega
EnvironmentFile=/etc/ega/options
ExecStartPre=/usr/local/bin/ega_create_socket_link.sh agent
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
echo "ega-inbox:/ega /ega  nfs   auto,noatime,nolock,bg,nfsvers=4,intr,tcp,actimeo=1800 0 0" >> /etc/fstab

# ================
echo "Starting the worker"
systemctl start ega-worker.service ega-socket-forwarder.service ega-socket-forwarder.socket

echo "Enabling services"
systemctl enable ega-worker.service ega-socket-forwarder.service ega-socket-forwarder.socket

echo "Workers ready"
