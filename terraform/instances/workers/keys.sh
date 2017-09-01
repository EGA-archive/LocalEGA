#!/bin/bash

set -e

# ========================
# No SELinux
echo "Disabling SElinux"
[ -f /etc/sysconfig/selinux ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/sysconfig/selinux
[ -f /etc/selinux/config ] && sed -i 's/SELINUX=.*/SELINUX=disabled/' /etc/selinux/config
setenforce 0

##############
# Public + Private parts
mkdir -p ~ega/.gnupg && chmod 700 ~ega/.gnupg
mkdir -p ~ega/.rsa && chmod 700 ~ega/.rsa
mkdir -p ~ega/.certs && chmod 700 ~ega/.certs
mkdir -p ~ega/.gnupg/private-keys-v1.d && chmod 700 ~ega/.gnupg/private-keys-v1.d

unzip /tmp/gpg.zip -d ~ega/.gnupg
unzip /tmp/gpg_private.zip -d ~ega/.gnupg/private-keys-v1.d
unzip /tmp/rsa.zip -d ~ega/.rsa
unzip /tmp/certs.zip -d ~ega/.certs

rm /tmp/gpg.zip
rm /tmp/gpg_private.zip
rm /tmp/rsa.zip
rm /tmp/certs.zip

chown -R ega:ega ~ega/.gnupg
chown -R ega:ega ~ega/.rsa
chown -R ega:ega ~ega/.certs

chmod 600 ~ega/.gnupg/{pubring.kbx,trustdb.gpg}
chmod -R 700 ~ega/.gnupg/private-keys-v1.d
chmod 640 ~ega/.certs/*.cert
chmod 600 ~ega/.certs/*.key
chmod 640 ~ega/.rsa/ega-public.pem
chmod 600 ~ega/.rsa/ega.pem

##############
git clone -b terraform https://github.com/NBISweden/LocalEGA.git ~/repo
pip3.6 install ~/repo/src

##############
EGA_SOCKET=$(su -c "gpgconf --list-dirs agent-extra-socket" - ega) # as ega user

cat > /etc/systemd/system/ega.slice <<EOF
[Unit]
Description=EGA Slice
DefaultDependencies=no
Before=slices.target

#[Slice]
#CPUShares=512
#MemoryLimit=2G
EOF

cat > /etc/systemd/system/ega-socket-proxy.socket <<EOF
[Unit]
Description=EGA GPG-agent (limited) socket activation
After=syslog.target
After=network.target

[Socket]
ListenStream=/run/ega/S.gpg-agent.extra
SocketUser=ega
SocketGroup=ega
SocketMode=0600
DirectoryMode=0755

[Install]
WantedBy=sockets.target
EOF

cat > /etc/systemd/system/ega-socket-proxy.service <<'EOF'
[Unit]
Description=EGA Socket Proxy service (GPG-master on port 9010)
After=syslog.target
After=network.target

Requires=ega-socket-proxy.socket

[Service]
Slice=ega.slice
Type=simple
User=ega
Group=ega
ExecStartPre=/usr/local/bin/gpg-agent --supervised
ExecStart=/bin/ega-socket-proxy 'ega-keys:9010' /run/ega/S.gpg-agent.extra --certfile $EGA_GPG_CERTFILE --keyfile $EGA_GPG_KEYFILE
#ExecReload=/usr/local/bin/gpgconf --reload gpg-agent

Environment=EGA_GPG_CERTFILE=~/.certs/selfsigned.cert
Environment=EGA_GPG_KEYFILE=~/.certs/selfsigned.key

StandardOutput=syslog
StandardError=syslog

Restart=on-failure
RestartSec=10
TimeoutSec=600

[Install]
WantedBy=multi-user.target
EOF

cat > ~ega/.gnupg/gpg-agent.conf <<EOF
#log-file gpg-agent.log
allow-preset-passphrase
default-cache-ttl 2592000 # one month
max-cache-ttl 31536000    # one year
pinentry-program /usr/local/bin/pinentry-curses
allow-loopback-pinentry
enable-ssh-support
extra-socket /run/ega/S.gpg-agent.extra
browser-socket /dev/null
disable-scdaemon
#disable-check-own-socket
EOF
chown ega:ega ~ega/.gnupg/gpg-agent.conf
chmod 640 ~ega/.gnupg/gpg-agent.conf

##############
echo "Starting the gpg-agent proxy"
systemctl start ega-socket-proxy.socket
systemctl start ega-socket-proxy.service

systemctl enable ega-socket-proxy.socket
systemctl enable ega-socket-proxy.service

